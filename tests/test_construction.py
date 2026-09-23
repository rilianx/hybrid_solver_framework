"""Constructor modular: bucle greedy del framework + vista constructiva + slot `greedy_score`."""

from __future__ import annotations

import textwrap
from random import Random

import pytest

from core.construction import GreedyConstructor
from core.validation import validate_component
from examples.lotsizing.construction import LatestSource, UnitMarginalCost
from examples.lotsizing.llm_spec import make_contexts
from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMP = {"name": "s", "slot": "greedy_score", "compatible_skeletons": ["SA"], "params": {}}


@pytest.fixture(scope="module")
def contexts():
    return make_contexts(n_contexts=2)


@pytest.mark.parametrize("n,T", [(3, 5), (10, 15)])
@pytest.mark.parametrize("rule", ["greedy", "rcl", "roulette"])
def test_greedy_constructor_is_feasible_and_deterministic_per_seed(n, T, rule):
    for k in range(3):
        inst = CLSPInstance.trigeiro(n, T, Random(700 + k), utilization=0.95, tbo=3.0)
        P = LotSizingModel(inst)
        g = GreedyConstructor(P, UnitMarginalCost(P), rule=rule, alpha=0.4)
        a, b = g.build(inst, Random(k)), g.build(inst, Random(k))
        assert P.is_feasible(a) and a == b
        assert g.fallbacks == 0


def test_unit_cost_score_beats_lot_for_lot_start():
    from examples.lotsizing.components import LotForLotConstructor

    inst = CLSPInstance.trigeiro(10, 15, Random(3), utilization=0.95, tbo=3.0)
    P = LotSizingModel(inst)
    greedy = P.objective(GreedyConstructor(P, UnitMarginalCost(P)).build(inst, Random(0)))
    assert greedy < 0.9 * P.objective(LotForLotConstructor().build(inst, Random(0)))


def test_dead_end_goes_to_the_view_fallback():
    class NoCandidates:
        def __init__(self):
            self.completed = False

        def empty(self):
            return "p"

        def candidates(self, p):
            return []

        def is_complete(self, p):
            return False

        def complete(self, p, rng):
            self.completed = True
            return "respaldo"

    view = NoCandidates()

    class P:
        def construction_view(self, inst):
            return view

    g = GreedyConstructor(P(), score=None)
    assert g.build(None, Random(0)) == "respaldo" and view.completed and g.fallbacks == 1
    with pytest.raises(ValueError):
        GreedyConstructor(P(), None, rule="nope")


def test_validator_accepts_reference_scores_and_rejects_broken_ones(contexts):
    ctx = contexts[0]
    for S in (UnitMarginalCost, LatestSource):
        assert validate_component(dict(COMP, name=S.__name__.lower()), S(ctx.problem), ctx).passed

    class Mutates:
        def score(self, p, a):
            p.used[0] += 1
            return 0.0

    class NaN:
        def score(self, p, a):
            return float("nan")

    for bad, check in ((Mutates(), "greedy_score.pure"), (NaN(), "greedy_score.finite")):
        report = validate_component(dict(COMP, name="bad"), bad, ctx)
        assert not report.passed and any(f.name == check for f in report.failures()), report.feedback()


def test_diversity_signature_separates_ideas_and_catches_copies():
    from core.validation.diversity import greedy_score_signature, similarity
    from examples.lotsizing.llm_spec import make_diversity_probe

    P = make_diversity_probe().problem
    unit, copy, latest = (greedy_score_signature(s, None, P) for s in (UnitMarginalCost(P), UnitMarginalCost(P), LatestSource(P)))
    assert similarity(unit, copy) == 1.0
    assert similarity(unit, latest) < 0.8


def test_catalog_wraps_scores_as_tunable_constructors():
    from examples.lotsizing.catalog import build_registry

    reg = build_registry()
    spec = reg.get("constructor", "greedy_unit_marginal_cost")
    assert set(spec.params) == {"rule", "alpha"} and spec.params["rule"]["values"] == ["greedy", "rcl", "roulette"]
    inst = CLSPInstance.trigeiro(5, 6, Random(1), utilization=0.9, tbo=2.0)
    P = LotSizingModel(inst)
    assert P.is_feasible(spec.make(P, rule="rcl", alpha=0.5).build(inst, Random(0)))
    # sin generados en greedy_score, el catálogo solo-generados no hereda los puntajes de mano
    assert [s.name for s in build_registry([], handwritten=False).for_slot("greedy_score")] == []


GOOD_SCORE = textwrap.dedent('''
    COMPONENT = {"name": "urgency_then_cost", "slot": "greedy_score",
                 "compatible_skeletons": ["SA", "ILS"], "requires": [],
                 "params": {"w": {"type": "float", "range": [0.0, 5.0]}}}


    class UrgencyThenCost:
        def __init__(self, problem, w=1.0):
            self.inst, self.w = problem.inst, w

        def score(self, partial, action):
            inst = self.inst
            setup = inst.setup_cost[action.item] if action.new_setup else 0.0
            hold = inst.holding_cost[action.item] * (action.period - action.source) * action.qty
            return (setup + self.w * hold) / max(action.qty, 1e-9)


    def build_component(problem, w=1.0):
        return UrgencyThenCost(problem, w)
''')


def test_generated_score_goes_through_the_llm_cycle_and_into_the_catalog(tmp_path):
    from examples.lotsizing.catalog import build_registry, load_generated
    from examples.lotsizing.llm_spec import make_spec
    from llm import ScriptedClient, generate_slot

    client = ScriptedClient(responses=[f"```python\n{GOOD_SCORE}\n```"])
    accepted, stats = generate_slot(client, make_spec(), "greedy_score", 1, make_contexts(n_contexts=1), tmp_path, verbose=False)
    assert [c.name for c in accepted] == ["urgency_then_cost"] and stats.accepted == 1
    assert "Vista constructiva" in client.calls[0][1]
    reg = build_registry(load_generated(tmp_path, verbose=False))
    spec = reg.get("constructor", "greedy_urgency_then_cost")
    assert {"rule", "alpha", "w"} <= set(spec.params)


def test_construction_types_import_from_the_problem_module():
    """El prompt indica importar desde el módulo del problema (corrida 10: ImportError)."""
    import examples.lotsizing.problem_model as pm
    from examples.lotsizing import construction

    assert pm.CoverAction is construction.CoverAction and pm.CLSPPartial is construction.CLSPPartial
