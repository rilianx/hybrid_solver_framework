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
    from dataclasses import replace

    spec = make_spec()
    # sin sonda: el veredicto lo dan solo las micro-instancias
    strict = [replace(c, diversity_probe=None) for c in make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=True)]
    client = ScriptedClient(responses=[fence(GOOD_SHIFT), fence(GOOD_SHIFT), fence(GOOD_SHIFT)])
    accepted, stats = generate_slot(client, spec, "neighborhood", 1, strict, tmp_path, max_rounds=3, verbose=False)
    assert accepted == [] and stats.abandoned == ["shift_setup_earlier"]
    assert stats.rejections_by_layer == {"quality": 3}
    correction = client.calls[1][1]
    assert "improves_from_start" in correction and "solución de PARTIDA" in correction
    assert "Desde dónde arranca el esqueleto" in client.calls[0][1]  # el prompt inicial ya la mostraba


def test_probe_rescues_neighborhood_that_only_improves_on_realistic_instances(tmp_path):
    """Corrida 7: `same_period_setup_swap` no mejoraba desde la partida en 3×5 (18 movimientos,
    ninguno mejora) pero sí en 10×15 (73 mejoras, todas novedosas). Rechazado, el modelo lo
    "arregló" rellenándolo con flips. La sonda da la última palabra sobre `improves_from_start`."""
    spec = make_spec()
    strict = make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=True)
    assert strict[0].diversity_probe is not None
    client = ScriptedClient(responses=[fence(GOOD_SHIFT)])
    accepted, stats = generate_slot(client, spec, "neighborhood", 1, strict, tmp_path, max_rounds=1, verbose=False)
    assert [c.name for c in accepted] == ["shift_setup_earlier"] and stats.rejections_by_layer == {}


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


REMOVAL_ONLY = textwrap.dedent('''
    COMPONENT = {"name": "removal_only", "slot": "neighborhood", "compatible_skeletons": ["SA"], "params": {}}

    class RemovalOnly:
        """Solo APAGA setups. Mejora desde lot-for-lot en instancias con holgura; en una
        instancia cuya solución trivial es óptimo local de flips, nada mejora."""
        def __init__(self, problem): self.problem = problem
        def moves(self, sol):
            return [(i, t) for i in range(len(sol)) for t in range(len(sol[i])) if sol[i][t]]
        def apply(self, sol, m):
            i, t = m; row = sol[i][:t] + (False,) + sol[i][t + 1:]
            return sol[:i] + (row,) + sol[i + 1:]
        def undo(self, sol, m):
            i, t = m; row = sol[i][:t] + (True,) + sol[i][t + 1:]
            return sol[:i] + (row,) + sol[i + 1:]
        def delta(self, sol, m):
            return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)

    def build_component(problem):
        return RemovalOnly(problem)
''')

NEVER_IMPROVES = textwrap.dedent('''
    COMPONENT = {"name": "never_improves", "slot": "neighborhood", "compatible_skeletons": ["SA"], "params": {}}

    class NeverImproves:
        """Movimientos válidos que no cambian nada: delta 0 siempre, undo trivialmente exacto."""
        def __init__(self, problem): self.problem = problem
        def moves(self, sol):
            return [(i, t) for i in range(len(sol)) for t in range(len(sol[i]))]
        def apply(self, sol, m): return sol
        def undo(self, sol, m): return sol
        def delta(self, sol, m): return 0.0

    def build_component(problem):
        return NeverImproves(problem)
''')


def test_improves_from_start_needs_only_one_context(tmp_path):
    """Corrida 4: `single_setup_removal_r1` era correcto y mejoraba desde la partida en la
    instancia Trigeiro, pero se rechazó porque en la otra micro-instancia la solución trivial
    era óptimo local de flips (nada mejora ahí). El gate estricto debe exigir mejora en AL
    MENOS un contexto, no en todos; las demás propiedades sí en todos."""
    from llm.generator import validate_generated_module

    contexts = make_contexts(n_contexts=2, strict=True)
    # sanity del escenario: la partida del 2º contexto no admite mejora por flips
    ref = contexts[1].reference_neighborhood
    sol = contexts[1].trivial_solutions[0]
    assert all(ref.delta(sol, m) >= -1e-9 for m in ref.moves(sol))

    p = tmp_path / "removal_only.py"; p.write_text(REMOVAL_ONLY)
    report, _, _ = validate_generated_module(p, contexts)
    assert report.passed, report.feedback()

    q = tmp_path / "never_improves.py"; q.write_text(NEVER_IMPROVES)
    report, _, _ = validate_generated_module(q, contexts)
    assert not report.passed and report.failed_layer == "quality"


ADD_ONLY = REMOVAL_ONLY.replace('"removal_only"', '"add_only"').replace("if sol[i][t]]", "if not sol[i][t]]") \
    .replace("(False,)", "(TMP,)").replace("(True,)", "(False,)").replace("(TMP,)", "(True,)")


def test_strict_feedback_lists_concrete_improving_moves():
    """Un operador que solo ENCIENDE setups mejora desde soluciones aleatorias (repara faltantes)
    pero no desde lot-for-lot factible: cae en `improves_from_start`, y el mensaje incluye los
    movimientos que SÍ mejoran según el vecindario de referencia (verdad-terreno), más la
    advertencia de no complicar el operador."""
    from core.validation import validate_component

    ctx = make_contexts(n_contexts=1, strict=True)[0]  # ctx0: Trigeiro, lot-for-lot factible
    ns = {}; exec(ADD_ONLY, ns)
    report = validate_component(ns["COMPONENT"], ns["build_component"](ctx.problem), ctx)
    assert not report.passed and any(f.name == "neighborhood.improves_from_start" for f in report.failures()), report.feedback()
    msg = report.feedback()
    assert "qué SÍ mejora" in msg and "APAGAR el setup del ítem" in msg and "NO compliques" in msg


def test_diversity_gate_rejects_duplicate_of_catalog_peer(tmp_path):
    """Corrida 5: con el gate estricto los tres vecindarios salieron con Jaccard 0,75–1,00
    entre sí y con el `setup_flip` escrito a mano — el gate embudona hacia el único operador
    que mejora. El gate de diversidad compara estructuralmente contra los ya aceptados y
    contra el catálogo, y pide una idea distinta, no otro nombre."""
    from examples.lotsizing.components import SetupFlipNeighborhood

    spec = make_spec()
    contexts = make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=False)
    peers = [("setup_flip", SetupFlipNeighborhood(contexts[0].problem))]

    # GOOD_SHIFT mueve un setup al período anterior: alcanza vecinos que un flip no alcanza
    client = ScriptedClient(responses=[fence(GOOD_SHIFT)])
    accepted, _ = generate_slot(client, spec, "neighborhood", 1, contexts, tmp_path,
                                catalog_peers=peers, verbose=False)
    assert [c.name for c in accepted] == ["shift_setup_earlier"]

    # un flip disfrazado con otro nombre y otra representación del movimiento: mismo vecindario
    disguised = textwrap.dedent('''
        COMPONENT = {"name": "toggle_disguised", "slot": "neighborhood", "compatible_skeletons": ["SA"], "params": {}}

        class ToggleDisguised:
            def __init__(self, problem): self.problem = problem
            def moves(self, sol):
                return [(t, i, "flip") for i in range(len(sol)) for t in range(len(sol[i]))]
            def apply(self, sol, m):
                t, i, _ = m; row = sol[i][:t] + (not sol[i][t],) + sol[i][t + 1:]
                return sol[:i] + (row,) + sol[i + 1:]
            def undo(self, sol, m): return self.apply(sol, m)
            def delta(self, sol, m):
                return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)

        def build_component(problem):
            return ToggleDisguised(problem)
    ''')
    client = ScriptedClient(responses=[fence(disguised)] * 4)
    accepted, stats = generate_slot(client, spec, "neighborhood", 1, contexts, tmp_path,
                                    max_rounds=2, catalog_peers=peers, verbose=False)
    assert accepted == [] and stats.rejections_by_layer == {"quality": 2}
    msg = client.calls[1][1]
    assert "setup_flip" in msg and "similitud 1.00" in msg and "IDEA" in msg


def test_diversity_gate_uses_the_probe_not_the_micro_instance(tmp_path):
    """El gate mide la diversidad sobre la sonda (instancia grande) reconstruyendo el
    componente allí: un flip disfrazado se rechaza aunque la validación de propiedades
    corra en micro-instancias de 2×4 (corrida 6: en 3×5 el Jaccard no discriminaba)."""
    from dataclasses import replace
    from random import Random

    from core.validation.base import DiversityProbe
    from examples.lotsizing.components import LotForLotConstructor, SetupFlipNeighborhood
    from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

    inst = CLSPInstance.trigeiro(10, 15, Random(100), utilization=0.95, tbo=3.0)
    big = LotSizingModel(inst)
    probe = DiversityProbe(problem=big, solution=LotForLotConstructor().build(inst, Random(0)))

    spec = make_spec()
    contexts = [replace(c, diversity_probe=probe) for c in make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=False)]
    peers = [("setup_flip", SetupFlipNeighborhood(big))]  # ligado al problema de la sonda

    disguised = textwrap.dedent('''
        COMPONENT = {"name": "toggle_disguised", "slot": "neighborhood", "compatible_skeletons": ["SA"], "params": {}}

        class ToggleDisguised:
            def __init__(self, problem): self.problem = problem
            def moves(self, sol):
                return [(t, i, "flip") for i in range(len(sol)) for t in range(len(sol[i]))]
            def apply(self, sol, m):
                t, i, _ = m; row = sol[i][:t] + (not sol[i][t],) + sol[i][t + 1:]
                return sol[:i] + (row,) + sol[i + 1:]
            def undo(self, sol, m): return self.apply(sol, m)
            def delta(self, sol, m):
                return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)

        def build_component(problem):
            return ToggleDisguised(problem)
    ''')
    client = ScriptedClient(responses=[fence(disguised)] * 4)
    accepted, stats = generate_slot(client, spec, "neighborhood", 1, contexts, tmp_path,
                                    max_rounds=2, catalog_peers=peers, verbose=False)
    assert accepted == [] and stats.rejections_by_layer == {"quality": 2}
    assert "setup_flip" in client.calls[1][1]


def test_token_counter_accumulates_and_reaches_stats(tmp_path):
    """El contador de tokens: el cliente informa el uso de cada llamada y
    `GenerationStats.tokens` lo acumula, incluidas las rondas de corrección."""
    from llm import TokenUsage

    spec = make_spec()
    contexts = make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=False)
    client = ScriptedClient(responses=[fence(GOOD_SHIFT)], usage_per_call=TokenUsage(4000, 900, reasoning_tokens=300))
    _, stats = generate_slot(client, spec, "neighborhood", 1, contexts, tmp_path, verbose=False)

    assert stats.tokens.calls == stats.llm_calls == 1
    assert stats.tokens.input_tokens == 4000 and stats.tokens.output_tokens == 900
    assert stats.tokens.total_tokens == 4900 and stats.tokens.reasoning_tokens == 300
    assert "4,900 tokens" in stats.summary()


def test_token_counter_is_optional(tmp_path):
    """Un cliente que no informa uso no rompe nada: el contador queda en cero."""
    spec = make_spec()
    contexts = make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=False)
    client = ScriptedClient(responses=[fence(GOOD_SHIFT)])
    _, stats = generate_slot(client, spec, "neighborhood", 1, contexts, tmp_path, verbose=False)
    assert stats.llm_calls == 1 and stats.tokens.total_tokens == 0
    assert "tokens" not in stats.summary()


def test_cost_estimate_comes_from_the_environment(monkeypatch):
    """Los precios no están cableados (cambian y dependen del proveedor): se leen del entorno."""
    from llm import TokenUsage, price_per_mtok

    used = TokenUsage(1_000_000, 100_000, calls=3)
    monkeypatch.delenv("LLM_PRICE_IN", raising=False)
    monkeypatch.delenv("LLM_PRICE_OUT", raising=False)
    assert price_per_mtok("gpt-5.4-mini") is None and used.cost_usd() is None
    assert "cost_usd" not in used.as_dict()

    monkeypatch.setenv("LLM_PRICE_IN", "0.25")
    monkeypatch.setenv("LLM_PRICE_OUT", "2.00")
    assert used.cost_usd() == pytest.approx(0.25 + 0.2)
    assert used.as_dict()["cost_usd"] == pytest.approx(0.45)


def test_novelty_gate_rejects_padding_with_flips(tmp_path):
    """Corrida 7: un operador que es `setup_flip` MENOS movimientos (subconjunto) o MÁS relleno
    que no mejora pasa el Jaccard (0,62 / 0,28), pero todo lo que mejora desde la partida lo
    mejora igual que `setup_flip`. `novel_improvements` lo rechaza y lo dice."""
    from dataclasses import replace
    from random import Random

    from core.validation.base import DiversityProbe
    from examples.lotsizing.components import LotForLotConstructor, SetupFlipNeighborhood
    from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

    inst = CLSPInstance.trigeiro(10, 15, Random(100), utilization=0.95, tbo=3.0)
    big = LotSizingModel(inst)
    probe = DiversityProbe(problem=big, solution=LotForLotConstructor().build(inst, Random(0)))
    contexts = [replace(c, diversity_probe=probe) for c in make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=False)]
    peers = [("setup_flip", SetupFlipNeighborhood(big))]

    # solo APAGAR setups: un subconjunto estricto de setup_flip (como `redundant_setup_pruner`)
    subset = textwrap.dedent('''
        COMPONENT = {"name": "only_off", "slot": "neighborhood", "compatible_skeletons": ["SA"], "params": {}}

        class OnlyOff:
            def __init__(self, problem): self.problem = problem
            def moves(self, sol):
                return [(i, t) for i in range(len(sol)) for t in range(len(sol[i])) if sol[i][t]]
            def apply(self, sol, m):
                i, t = m; row = sol[i][:t] + (not sol[i][t],) + sol[i][t + 1:]
                return sol[:i] + (row,) + sol[i + 1:]
            def undo(self, sol, m): return self.apply(sol, m)
            def delta(self, sol, m):
                return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)

        def build_component(problem):
            return OnlyOff(problem)
    ''')
    client = ScriptedClient(responses=[fence(subset)] * 2)
    accepted, stats = generate_slot(client, spec := make_spec(), "neighborhood", 1, contexts, tmp_path,
                                    max_rounds=1, catalog_peers=peers, verbose=False)
    assert accepted == [] and stats.rejections_by_layer == {"quality": 1}
    # y el reporte nombra la propiedad y al par (queda en el módulo rechazado -> feedback de la ronda 2)
    from llm.generator import validate_generated_module
    report, _, _ = validate_generated_module(next(tmp_path.glob("neighborhood/*.py")), contexts, peers=peers)
    msg = report.feedback()
    assert "novel_improvements" in msg and "setup_flip" in msg and "no cuenta como idea nueva" in msg


def test_probe_checks_constructor_feasibility_on_realistic_instance(tmp_path):
    """`constructor.feasible` se juzga en 3×5; la sonda repite la comprobación en 10×15, donde
    10 ítems compiten por la capacidad y un greedy que allí deja faltante es inútil como partida."""
    from core.validation.quality import probe_checks
    from examples.lotsizing.llm_spec import make_diversity_probe

    probe = make_diversity_probe()

    class OneSetupPerItem:
        """Enciende solo el primer período con demanda de cada ítem: factible en micro-instancias
        holgadas, infactible cuando la capacidad del primer período no alcanza para todos."""

        def build(self, inst, rng):
            return tuple(
                tuple(t == next((tt for tt in range(inst.n_periods) if inst.demand[i][tt] > 0), 0) for t in range(inst.n_periods))
                for i in range(inst.n_items)
            )

    res = probe_checks("constructor", OneSetupPerItem(), probe)
    assert [r.name for r in res] == ["constructor.feasible_on_probe"] and not res[0].passed
    assert "tamaño realista" in res[0].message and "ACUMULADA" in res[0].message

    from examples.lotsizing.components import LotForLotConstructor

    res = probe_checks("constructor", LotForLotConstructor(), probe)
    assert res and res[0].passed
    assert probe_checks("neighborhood", object(), probe) == []
