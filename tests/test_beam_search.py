"""Beam search constructiva (`core.beam_search`) sobre la vista del CLSP y del CVRP, y su
registro en el catálogo como `beam_<puntaje>`."""

from __future__ import annotations

from random import Random

import pytest

from core.beam_search import BeamSearchConstructor
from core.construction import GreedyConstructor
from examples.cvrp.construction import CheapestInsertion
from examples.cvrp.problem_model import CVRPInstance, CVRPModel
from examples.lotsizing.construction import UnitMarginalCost
from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel


def _cvrp(seed=0, n=12):
    inst = CVRPInstance.random(n, Random(seed))
    return inst, CVRPModel(inst)


def test_rollout_beam_is_never_worse_than_its_greedy():
    """El rollout desde la raíz es la solución greedy, y la mejor solución vista nunca empeora."""
    for seed in range(3):
        inst, P = _cvrp(seed)
        greedy = P.objective(GreedyConstructor(P, CheapestInsertion(P)).build(inst, Random(0)))
        bs = BeamSearchConstructor(P, CheapestInsertion(P), beam_width=3, branching=3)
        sol = bs.build(inst, Random(0))
        assert P.is_feasible(sol)
        assert P.objective(sol) <= greedy + 1e-9
        assert bs.rollouts > 1 and bs.levels > 1


def test_score_beam_with_width_one_and_branching_one_is_the_greedy():
    inst, P = _cvrp(4)
    score = CheapestInsertion(P)
    greedy = GreedyConstructor(P, score).build(inst, Random(0))
    bs = BeamSearchConstructor(P, score, evaluation="score", beam_width=1, branching=1).build(inst, Random(0))
    assert P.objective(bs) == pytest.approx(P.objective(greedy))


def test_beam_is_deterministic_and_feasible_on_clsp():
    inst = CLSPInstance.trigeiro(4, 6, Random(11), utilization=0.9, tbo=2.0)
    P = LotSizingModel(inst)
    bs = BeamSearchConstructor(P, UnitMarginalCost(P), beam_width=2, branching=2, max_seconds=5)
    a, b = bs.build(inst, Random(0)), bs.build(inst, Random(0))
    assert P.is_feasible(a) and a == b


def test_invalid_configurations_are_rejected():
    inst, P = _cvrp()
    with pytest.raises(ValueError):
        BeamSearchConstructor(P, evaluation="score")
    with pytest.raises(ValueError):
        BeamSearchConstructor(P, branching=2)
    with pytest.raises(ValueError):
        BeamSearchConstructor(P, CheapestInsertion(P), evaluation="nope")


def test_beam_constructor_spec_enters_the_catalog():
    from core.component import ComponentSpec
    from llm.catalog import beam_constructor_spec

    score_spec = ComponentSpec.from_dict(
        {"name": "cheapest_insertion", "slot": "greedy_score", "compatible_skeletons": ["SA"], "params": {}},
        lambda problem: CheapestInsertion(problem))
    spec = beam_constructor_spec(score_spec, ["SA"])
    assert spec.name == "beam_cheapest_insertion" and spec.slot == "constructor"
    assert spec.default_params() == {"beam_width": 4, "branching": 4}
    inst, P = _cvrp(2)
    c = spec.make(P, beam_width=2, branching=2)
    assert isinstance(c, BeamSearchConstructor) and P.is_feasible(c.build(inst, Random(0)))


def test_pack_flag_registers_beam_constructors():
    from dataclasses import replace

    from examples.cvrp.pack import PACK
    from llm.catalog import build_registry

    names = {s.name for s in build_registry(PACK).for_slot("constructor")}
    assert not any(n.startswith("beam_") for n in names)
    names = {s.name for s in build_registry(replace(PACK, beam_constructors=True)).for_slot("constructor")}
    assert "beam_cheapest_insertion" in names
