"""Ciclo generar → validar → corregir (§6) con un LLM guionado: una respuesta
con un componente correcto y otro roto, y la corrección en la segunda ronda.
También: parser, prompts (contienen el Protocol y el ejemplo few-shot) y
abandono tras `max_rounds`."""

import textwrap

import pytest

pytest.importorskip("pulp")

from examples.lotsizing.llm_spec import make_contexts, make_spec
from llm import ScriptedClient, generate_slot
from llm.parser import component_name, extract_code_blocks, parse_response
from llm.prompts import correction_prompt, generation_prompt

GOOD_SHIFT = textwrap.dedent('''
    COMPONENT = {
        "name": "shift_setup_earlier",
        "slot": "neighborhood",
        "compatible_skeletons": ["SA", "ILS"],
        "requires": ["ProblemModel.objective"],
        "params": {},
    }


    class ShiftSetupEarlier:
        """Mueve un setup (i, t) al período anterior t-1 si allí no había setup."""

        def __init__(self, problem):
            self.problem = problem

        def moves(self, sol):
            for i, row in enumerate(sol):
                for t in range(1, len(row)):
                    if row[t] and not row[t - 1]:
                        yield (i, t)

        def apply(self, sol, m):
            i, t = m
            row = list(sol[i]); row[t] = False; row[t - 1] = True
            return sol[:i] + (tuple(row),) + sol[i + 1:]

        def undo(self, sol, m):
            i, t = m
            row = list(sol[i]); row[t] = True; row[t - 1] = False
            return sol[:i] + (tuple(row),) + sol[i + 1:]

        def delta(self, sol, m):
            return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


    def build_component(problem):
        return ShiftSetupEarlier(problem)
''')

# Error típico: `delta` con signo invertido ("siempre mejora").
BAD_TOGGLE = textwrap.dedent('''
    COMPONENT = {
        "name": "toggle_setup",
        "slot": "neighborhood",
        "compatible_skeletons": ["SA", "ILS"],
        "requires": ["ProblemModel.objective"],
        "params": {},
    }


    class ToggleSetup:
        def __init__(self, problem):
            self.problem = problem

        def moves(self, sol):
            for i in range(len(sol)):
                for t in range(len(sol[i])):
                    yield (i, t)

        def apply(self, sol, m):
            i, t = m
            row = list(sol[i]); row[t] = not row[t]
            return sol[:i] + (tuple(row),) + sol[i + 1:]

        def undo(self, sol, m):
            return self.apply(sol, m)

        def delta(self, sol, m):
            return self.problem.objective(sol) - self.problem.objective(self.apply(sol, m))


    def build_component(problem):
        return ToggleSetup(problem)
''')

FIXED_TOGGLE = BAD_TOGGLE.replace(
    "return self.problem.objective(sol) - self.problem.objective(self.apply(sol, m))",
    "return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)",
)

NO_FACTORY = textwrap.dedent('''
    COMPONENT = {"name": "no_factory", "slot": "neighborhood", "compatible_skeletons": ["SA"], "params": {}}

    class NoFactory:
        def moves(self, sol): return []
        def apply(self, sol, m): return sol
        def undo(self, sol, m): return sol
        def delta(self, sol, m): return 0.0
''')


def fence(*sources: str) -> str:
    return "\n".join(f"Variante:\n```python\n{s}\n```" for s in sources)


@pytest.fixture(scope="module")
def spec_and_ctx():
    # strict=False: `shift_setup_earlier` es correcto pero inerte desde lot-for-lot; el ciclo
    # de este test verifica corrección contractual, no utilidad desde la partida.
    return make_spec(), make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=False)


def test_parser_extracts_blocks_and_names():
    mods = parse_response(fence(GOOD_SHIFT, BAD_TOGGLE))
    assert [m.name for m in mods] == ["shift_setup_earlier", "toggle_setup"]
    assert extract_code_blocks("texto sin bloques de código") == []
    assert component_name("def x(: pass") is None


def test_generation_prompt_contains_contract_fewshot_and_problem(spec_and_ctx):
    spec, _ = spec_and_ctx
    p = generation_prompt(spec, "neighborhood", 3)
    assert "class Neighborhood(Protocol)" in p
    assert "def delta(self, sol" in p
    assert "swap_in_out" in p  # few-shot de knapsack
    assert "CLSP" in p and "y_{i}_{t}" in p
    assert "3 componentes ESTRUCTURALMENTE DISTINTOS" in p


def test_correction_prompt_carries_feedback_and_source(spec_and_ctx):
    spec, _ = spec_and_ctx
    p = correction_prompt(spec, "neighborhood", BAD_TOGGLE, "delta_consistent: delta=-3 pero f(apply)-f(sol)=3")
    assert "RECHAZADO" in p and "delta=-3" in p and "class ToggleSetup" in p


def test_generate_validate_correct_cycle(spec_and_ctx, tmp_path):
    spec, contexts = spec_and_ctx
    client = ScriptedClient(responses=[fence(GOOD_SHIFT, BAD_TOGGLE), fence(FIXED_TOGGLE)])

    accepted, stats = generate_slot(client, spec, "neighborhood", 2, contexts, tmp_path, max_rounds=3, verbose=False)

    assert sorted(c.name for c in accepted) == ["shift_setup_earlier", "toggle_setup"]
    assert stats.parsed == 2 and stats.accepted == 2 and stats.llm_calls == 2
    assert stats.rejections_by_layer == {"contractual": 1}
    assert stats.rounds_per_accepted == {"shift_setup_earlier": 1, "toggle_setup": 2}
    # el prompt de corrección llevó el feedback concreto del validador
    assert "delta_consistent" in client.calls[1][1]
    # los módulos quedaron en disco por ronda
    assert (tmp_path / "neighborhood" / "toggle_setup_r1.py").exists()
    assert (tmp_path / "neighborhood" / "toggle_setup_r2.py").exists()
    # y el componente aceptado es usable
    impl = accepted[0].build_component(contexts[0].problem)
    assert list(impl.moves(contexts[0].trivial_solutions[0])) != []


def test_abandons_after_max_rounds(spec_and_ctx, tmp_path):
    spec, contexts = spec_and_ctx
    client = ScriptedClient(responses=[fence(NO_FACTORY), fence(NO_FACTORY)])
    accepted, stats = generate_slot(client, spec, "neighborhood", 1, contexts, tmp_path, max_rounds=2, verbose=False)
    assert accepted == []
    assert stats.abandoned == ["no_factory"]
    assert stats.rejections_by_layer == {"syntactic": 2}


def test_strict_contexts_reject_neighborhood_inert_from_start(tmp_path):
    """Modo generación (strict=True): un vecindario correcto pero que no mejora desde la
    solución de partida se rechaza con un mensaje que explica por qué, y el prompt de
    corrección lleva la solución de partida para que el modelo la vea."""
    spec = make_spec()
    strict = make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=True)
    client = ScriptedClient(responses=[fence(GOOD_SHIFT), fence(GOOD_SHIFT), fence(GOOD_SHIFT)])
    accepted, stats = generate_slot(client, spec, "neighborhood", 1, strict, tmp_path, max_rounds=3, verbose=False)
    assert accepted == [] and stats.abandoned == ["shift_setup_earlier"]
    assert stats.rejections_by_layer == {"quality": 3}
    correction = client.calls[1][1]
    assert "improves_from_start" in correction and "solución de PARTIDA" in correction
    assert "Desde dónde arranca el esqueleto" in client.calls[0][1]  # el prompt inicial ya la mostraba


def test_infeasible_constructor_feedback_says_where_demand_is_missing():
    """El feedback de `constructor.feasible` incluye ítem/período/cantidad y la regla del
    problema — lo que le faltó al `rolling_horizon_cover_constructor` abandonado."""
    from core.validation import validate_component

    ctx = make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=False)[0]

    class NoSetups:
        def build(self, inst, rng):
            return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    report = validate_component({"name": "no_setups", "slot": "constructor"}, NoSetups(), ctx)
    msg = report.feedback()
    assert "constructor.feasible" in msg and "faltante total" in msg and "ítem 0 período" in msg
    assert "sin backlog" in msg and "no tiene ningún setup" in msg
