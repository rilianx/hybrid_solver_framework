"""El CPMP en el ciclo completo (`llm.cycle`), con un LLM guionado: un modelo SIN vista MIP y con
vista constructiva, su pack (solo el esqueleto CONSTRUCT, con beam search), un puntaje generado
contra la vista generada y el tuning del constructor."""

from __future__ import annotations

import shutil
import textwrap
import uuid
from pathlib import Path
from random import Random

import pytest

from core.model_parts import PartsModel, has_construction, has_mip
from examples.cpmp import model_parts as ref
from examples.cpmp.cases import bfs_optimum, load_cases
from llm.cycle import load_variant, model_path, run_model_stage


def _ref_sources() -> tuple[str, str]:
    """La referencia partida en lo que escribiría el LLM en cada etapa."""
    src = Path(ref.__file__).read_text()
    head, view = src.split("# ---------------------------------------------------------------- vista constructiva")
    return head, "from __future__ import annotations\n\nfrom random import Random\n\n" + view


SCORE = textwrap.dedent('''
    COMPONENT = {"name": "fill_sorted_first", "slot": "greedy_score", "compatible_skeletons": ["CONSTRUCT"],
                 "requires": [], "params": {}}


    class FillSortedFirst:
        """Poner un contenedor sobre una pila ordenada de grupo mayor o igual (el de menor diferencia);
        si no hay, sacar de la pila más baja hacia la más baja."""

        def __init__(self, problem):
            self.problem = problem

        def score(self, partial, action):
            stacks = partial[0]
            so, sd = action
            ordered = lambda s: all(s[k] >= s[k + 1] for k in range(len(s) - 1))
            top = lambda s: s[-1] if s else self.problem.inst.G
            if not ordered(stacks[so]) and ordered(stacks[sd]) and top(stacks[sd]) >= top(stacks[so]):
                return float(top(stacks[sd]) - top(stacks[so]))
            return 1000.0 + 10.0 * len(stacks[so]) + len(stacks[sd])


    def build_component(problem, **params):
        return FillSortedFirst(problem)
''')


def test_cases_have_exact_optima_and_the_reference_is_valid_without_mip():
    from core.validation.model_parts import validate_parts
    from examples.cpmp.pack import PACK

    cases = load_cases()
    assert all(c.optimum == len(bfs_optimum(c.instance)) for c in cases[:3])
    assert not has_mip(ref) and has_construction(ref)
    report = validate_parts(ref, cases, scale_instances=PACK.make_instances(1, 777, PACK.parse_size(PACK.default_size)))
    assert report.passed, report.feedback()


def test_a_bad_lower_bound_is_rejected():
    import types

    from core.validation.model_parts import check_construction_view

    m = types.SimpleNamespace(**{k: getattr(ref, k) for k in dir(ref) if not k.startswith("__")})
    m.partial_lower_bound = lambda inst, p: float(len(p[1]) + 2 * ref._bad(p[0]) + 5)
    r = check_construction_view(m, load_cases())
    assert not r.passed and "lower_bound_valid" in r.feedback()


def test_the_reference_variant_is_a_constructive_only_pack():
    from llm.catalog import build_registry

    pack = load_variant("cpmp", "moves", None, reference=True)
    assert pack.skeletons == ["CONSTRUCT"] and pack.beam_constructors
    assert {s.name for s in build_registry(pack).for_slot("constructor")} == {"trivial"}
    spec = pack.make_spec()
    assert "NO tiene vista MIP" in spec.variable_naming and "def candidates" in spec.construction_source
    inst = pack.make_instances(1, 3, pack.parse_size("4x4"))[0]
    P = pack.problem_factory(inst)
    with pytest.raises(NotImplementedError):
        P.build_mip(inst)
    view = P.construction_view(inst)
    assert callable(view.lower_bound) and view.key(view.empty()) == tuple(tuple(s) for s in inst.stacks)


def test_the_model_stage_without_mip_and_the_next_stages():
    """model (guionado: heurística + constructiva rota y corregida) → pack del modelo generado →
    puntaje generado → greedy y beam en CONSTRUCT."""
    from core.assembler import ALL_SKELETONS, Assembler
    from core.beam_search import BeamSearchConstructor
    from core.construction import GreedyConstructor
    from llm import ScriptedClient, generate_slot
    from llm.catalog import build_registry

    heur, view = _ref_sources()
    # ofrece también mover una pila sobre sí misma: un movimiento inválido que termina en una solución infactible
    broken = view.replace("if so != sd and stacks[so]", "if stacks[so]")
    assert broken != view
    ws = Path("generated") / f"test_cpmp_cycle_{uuid.uuid4().hex[:8]}"
    try:
        client = ScriptedClient(responses=[f"```python\n{heur}\n```", f"```python\n{broken}\n```", f"```python\n{view}\n```"])
        stats = run_model_stage("cpmp", "moves", ws, client, rounds=2)
        assert stats["accepted"] and stats["construction_accepted"], stats["rejections"]
        assert stats["mip_rounds"] == 0 and stats["construction_rounds"] == 2 and stats["llm_calls"] == 3
        # la etapa constructiva no pidió la vista MIP ni vio a FRG
        assert "def variables(inst)" not in client.calls[1][1] and "frg" not in client.calls[1][1].lower()
        assert "# ---- vista MIP ----" not in model_path(ws).read_text()

        pack = load_variant("cpmp", "moves", ws, reference=False)
        assert pack.skeletons == ["CONSTRUCT"] and pack.beam_constructors
        spec = pack.make_spec()
        ctxs = pack.make_contexts(n_contexts=1, strict=False)
        from dataclasses import replace

        ctxs = [replace(c, constructor_max_relative_gap=50.0, diversity_probe=None) for c in ctxs]  # se prueba el ciclo
        accepted, st = generate_slot(ScriptedClient(responses=[f"Variante:\n```python\n{SCORE}\n```"]), spec, "greedy_score",
                                     1, ctxs, ws / "components", max_rounds=1, verbose=False)
        assert [c.name for c in accepted] == ["fill_sorted_first"], st.rejections_by_layer

        registry = build_registry(pack, accepted)
        assert {"trivial", "greedy_fill_sorted_first", "beam_fill_sorted_first"} <= {s.name for s in registry.for_slot("constructor")}
        A = Assembler(problem_factory=pack.problem_factory, registry=registry, skeletons={"CONSTRUCT": ALL_SKELETONS["CONSTRUCT"]})
        cases = load_cases()
        insts = [c.instance for c in cases[:3]]
        optimum = sum(c.optimum for c in cases[:3]) / 3
        for name in ("trivial", "greedy_fill_sorted_first", "beam_fill_sorted_first"):
            cost = A.evaluate(A.default_config("CONSTRUCT", {"constructor": name}), insts, 1.0, on_error="raise")
            assert optimum - 1e-9 <= cost < A.penalty_cost
        P = pack.problem_factory(cases[1].instance)
        impl = accepted[0].build_component(P)
        g = P.objective(GreedyConstructor(P, impl).build(cases[1].instance, Random(0)))
        b = P.objective(BeamSearchConstructor(P, impl, beam_width=3, branching=3).build(cases[1].instance, Random(0)))
        assert b <= g
    finally:
        shutil.rmtree(ws, ignore_errors=True)
