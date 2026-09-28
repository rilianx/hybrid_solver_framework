"""Del problema al algoritmo sin código del problema escrito a mano (§6.1), con el CPMP y un LLM
guionado: descripción + casos → modelo por piezas SIN vista MIP y CON vista constructiva →
pack armado sobre el modelo generado → puntaje generado → greedy y beam search en CONSTRUCT."""

from __future__ import annotations

import textwrap
import types
from dataclasses import replace
from pathlib import Path
from random import Random

import pytest

from core.model_parts import PartsModel
from core.validation.model_parts import check_construction_view, check_heuristic_view
from examples.cpmp import model_parts as ref
from examples.cpmp.cases import bfs_optimum, load_cases


@pytest.fixture(scope="module")
def cases():
    return load_cases()


def _ref_sources() -> tuple[str, str]:
    """La referencia partida en lo que escribiría el LLM en cada etapa."""
    src = Path(ref.__file__).read_text()
    marker = "# ---------------------------------------------------------------- vista constructiva"
    head, view = src.split(marker)
    return head, "from __future__ import annotations\n\nfrom random import Random\n\n" + view


def mutant_view(**overrides):
    """Las piezas de referencia con la vista constructiva envuelta y algunos métodos reemplazados."""
    m = types.SimpleNamespace(**{k: getattr(ref, k) for k in dir(ref) if not k.startswith("__")})

    def construction_view(inst):
        view = ref.construction_view(inst)
        for name, fn in overrides.items():
            setattr(view, name, types.MethodType(fn, view))
        return view

    m.construction_view = construction_view
    return m


# --- casos y validación de la vista constructiva ---------------------------------------
def test_cases_have_exact_optima_and_the_reference_passes(cases):
    assert all(c.optimum == len(bfs_optimum(c.instance)) for c in cases[:3])
    assert check_heuristic_view(ref, cases).passed
    report = check_construction_view(ref, cases)
    assert report.passed, report.feedback()


def test_an_apply_that_mutates_the_partial_is_rejected(cases):
    def apply(self, p, a):
        p.moves = p.moves + (a,)
        return ref._View.apply(self, p, a)

    r = check_construction_view(mutant_view(apply=apply), cases)
    assert not r.passed and "apply_pure" in r.feedback()


def test_a_view_that_can_cycle_is_rejected(cases):
    def candidates(self, p):  # sin evitar layouts repetidos ni tope de pasos
        if p.bad() == 0:
            return []
        return [(so, sd) for so in range(len(p.stacks)) for sd in range(len(p.stacks))
                if so != sd and p.stacks[so] and len(p.stacks[sd]) < p.H]

    r = check_construction_view(mutant_view(candidates=candidates), cases)
    assert not r.passed and "terminates" in r.feedback()


def test_an_infeasible_fallback_is_rejected(cases):
    def candidates(self, p):
        return []  # siempre callejón sin salida

    def complete(self, p, rng):
        return ref.canonical(p.moves)  # no ordena

    r = check_construction_view(mutant_view(candidates=candidates, complete=complete), cases)
    assert not r.passed and "solution_feasible" in r.feedback() and "orden" in r.feedback()


def test_an_invalid_lower_bound_is_rejected(cases):
    def lower_bound(self, p):
        return len(p.moves) + 2 * p.bad() + 5

    r = check_construction_view(mutant_view(lower_bound=lower_bound), cases)
    assert not r.passed and "lower_bound_valid" in r.feedback()


# --- generación del modelo: heurística + constructiva, sin MIP -------------------------
def _generate(tmp_path, cases):
    from examples.cpmp.pack import PACK
    from llm import ScriptedClient
    from llm.parts_generator import generate_problem_model_parts

    heur, view = _ref_sources()
    broken = view.replace("return Partial(self._after(p, so, sd), p.H, p.G, p.moves + ((so, sd),), p.seen)",
                          "p.moves = p.moves + ((so, sd),)\n        return Partial(self._after(p, so, sd), p.H, p.G, p.moves, p.seen)")
    assert broken != view
    client = ScriptedClient(responses=[f"```python\n{heur}\n```", f"```python\n{broken}\n```", f"```python\n{view}\n```"])
    res = generate_problem_model_parts(client, PACK.make_model_spec(), cases, tmp_path, verbose=False)
    return res, client, heur


def test_model_generation_without_mip_and_with_a_constructive_view(tmp_path, cases):
    res, client, heur = _generate(tmp_path, cases)
    assert res.heuristic.accepted and res.mip.rounds == 0 and res.construction.accepted
    assert res.construction.rounds == 2 and res.llm_calls == 3 and "apply_pure" in res.construction.reports[0]
    assert res.path is not None and res.path.name == "model_constructive_r2.py"
    # el prompt de la vista constructiva trae el modelo aprobado y el contrato, y no pide MIP
    prompt = client.calls[1][1]
    assert "construction_view(inst)" in prompt and heur.strip()[-200:] in prompt and "def variables(inst)" not in prompt
    assert "frg" not in prompt.lower()
    P = PartsModel(__import__("llm.generated_pack", fromlist=["x"]).load_generated_model(res.path, "cpmp_test"), cases[0].instance)
    assert not P.has_mip
    with pytest.raises(NotImplementedError):
        P.build_mip(cases[0].instance)


# --- pack sobre el modelo generado: puntaje generado, greedy y beam en CONSTRUCT --------
SCORE = textwrap.dedent('''
    COMPONENT = {"name": "fill_sorted_first", "slot": "greedy_score", "compatible_skeletons": ["CONSTRUCT"],
                 "requires": [], "params": {}}


    class FillSortedFirst:
        """Poner un contenedor sobre una pila ordenada de grupo mayor o igual (el de menor
        diferencia); si no hay, sacar de la pila más baja hacia la más baja."""

        def __init__(self, problem):
            self.problem = problem

        def score(self, partial, action):
            so, sd = action
            c = partial.g(so)
            if not partial.is_sorted_stack(so) and partial.is_sorted_stack(sd) and partial.g(sd) >= c:
                return float(partial.g(sd) - c)
            return 1000.0 + 10.0 * partial.h(so) + partial.h(sd)


    def build_component(problem, **params):
        return FillSortedFirst(problem)
''')


def test_pipeline_on_the_generated_model(tmp_path, cases):
    from core.assembler import ALL_SKELETONS, Assembler
    from core.construction import GreedyConstructor
    from examples.cpmp.pack import PACK
    from llm import ScriptedClient, generate_slot
    from llm.catalog import build_registry
    from llm.generated_pack import pack_from_generated_model

    res, _, _ = _generate(tmp_path / "model", cases)
    gpack = pack_from_generated_model(PACK, res.path)
    assert gpack.skeletons == ["CONSTRUCT"] and gpack.beam_constructors
    assert {s.name for s in build_registry(gpack).for_slot("constructor")} == {"trivial"}  # nada del problema a mano
    spec = gpack.make_spec()
    assert "construction_view" in spec.problem_model_source and "frg" not in spec.problem_model_source.lower()

    # el LLM (guionado) escribe un puntaje contra la vista GENERADA; umbral laxo: se prueba el ciclo
    ctxs = [replace(c, constructor_max_relative_gap=50.0, diversity_probe=None) for c in gpack.make_contexts(n_contexts=1)]
    accepted, stats = generate_slot(ScriptedClient(responses=[f"Variante:\n```python\n{SCORE}\n```"]), spec, "greedy_score", 1,
                                    ctxs, tmp_path / "gen", max_rounds=1, verbose=False)
    assert [c.name for c in accepted] == ["fill_sorted_first"], stats.rejections_by_layer

    registry = build_registry(gpack, accepted)
    names = {s.name for s in registry.for_slot("constructor")}
    assert {"trivial", "greedy_fill_sorted_first", "beam_fill_sorted_first"} <= names
    A = Assembler(problem_factory=gpack.problem_factory, registry=registry, skeletons={"CONSTRUCT": ALL_SKELETONS["CONSTRUCT"]})
    insts = [c.instance for c in cases[:3]]
    for name in ("trivial", "greedy_fill_sorted_first", "beam_fill_sorted_first"):
        cost = A.evaluate(A.default_config("CONSTRUCT", {"constructor": name}), insts, 1.0, on_error="raise")
        assert cost < A.penalty_cost
        optimum = sum(c.optimum for c in cases[:3]) / 3
        assert cost >= optimum - 1e-9  # nunca mejor que el óptimo exacto de los casos
    # la beam search sobre el modelo generado no es peor que el greedy del mismo puntaje
    P = gpack.problem_factory(cases[1].instance)
    impl = accepted[0].build_component(P)
    from core.beam_search import BeamSearchConstructor

    g = P.objective(GreedyConstructor(P, impl).build(cases[1].instance, Random(0)))
    b = P.objective(BeamSearchConstructor(P, impl, beam_width=3, branching=3).build(cases[1].instance, Random(0)))
    assert b <= g
