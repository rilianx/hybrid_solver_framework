"""Constructor modular: bucle greedy del framework + vista constructiva + slot `greedy_score`."""

from __future__ import annotations

from random import Random

import pytest

from core.construction import GreedyConstructor
from core.validation import validate_component
from examples.lotsizing.construction import LatestSource, UnitMarginalCost
from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel
from tests.contexts import clsp_contexts, clsp_diversity_probe

COMP = {"name": "s", "slot": "greedy_score", "compatible_skeletons": ["SA"], "params": {}}


@pytest.fixture(scope="module")
def contexts():
    return clsp_contexts(n_contexts=2)


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
    P = clsp_diversity_probe().problem
    unit, copy, latest = (greedy_score_signature(s, None, P) for s in (UnitMarginalCost(P), UnitMarginalCost(P), LatestSource(P)))
    assert similarity(unit, copy) == 1.0
    assert similarity(unit, latest) < 0.8


def test_catalog_wraps_scores_as_tunable_constructors():
    from core.catalog import build_registry
    from examples.lotsizing.pack import PACK

    reg = build_registry(PACK)
    spec = reg.get("constructor", "greedy_unit_marginal_cost")
    assert set(spec.params) == {"rule", "alpha"} and spec.params["rule"]["values"] == ["greedy", "rcl", "roulette"]
    inst = CLSPInstance.trigeiro(5, 6, Random(1), utilization=0.9, tbo=2.0)
    P = LotSizingModel(inst)
    assert P.is_feasible(spec.make(P, rule="rcl", alpha=0.5).build(inst, Random(0)))


def test_construction_types_import_from_the_problem_module():
    """Los tipos de la vista constructiva se importan también desde el módulo del problema."""
    import examples.lotsizing.problem_model as pm
    from examples.lotsizing import construction

    assert pm.CoverAction is construction.CoverAction and pm.CLSPPartial is construction.CLSPPartial
