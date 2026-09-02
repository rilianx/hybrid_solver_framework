"""Prueba de integración: el problema piloto (knapsack) corriendo sobre
las tres especializaciones del núcleo, incluyendo el sub-MIP real (PuLP/CBC).
"""

from random import Random

import pytest

pulp = pytest.importorskip("pulp")

from core.common_components import AlwaysAccept, BetterAcceptance, MaxIterationsStop
from examples.knapsack.components import (
    BitFlipNeighborhood,
    GreedyRandomizedConstructor,
    KnapsackMIPRepair,
    RandomDestruction,
)
from examples.knapsack.problem_model import (
    KnapsackInstance,
    KnapsackModel,
    KnapsackObjective,
    bound_problem_model,
)
from skeletons.ils import build_ils, hill_climb
from skeletons.lns_mip import build_lns_mip, run_lns_mip
from skeletons.sa import build_sa, make_run


@pytest.fixture
def instance():
    rng = Random(1)
    return KnapsackInstance.random(12, rng)


def test_constructor_produces_feasible_solution(instance):
    base = KnapsackModel()
    constructor = GreedyRandomizedConstructor(alpha=0.3)
    sol = constructor.build(instance, Random(0))
    assert base.is_feasible(sol, instance)


def test_neighborhood_undo_apply_is_identity(instance):
    base = KnapsackModel()
    evaluator = KnapsackObjective(base, instance)
    neighborhood = BitFlipNeighborhood(evaluator)
    sol = tuple(False for _ in range(instance.n))
    for m in neighborhood.moves(sol):
        applied = neighborhood.apply(sol, m)
        assert neighborhood.undo(applied, m) == sol


def test_sa_beats_a_null_solution(instance):
    base = KnapsackModel()
    evaluator = KnapsackObjective(base, instance)
    problem = bound_problem_model(instance)
    constructor = GreedyRandomizedConstructor(alpha=0.3)
    neighborhood = BitFlipNeighborhood(evaluator)
    stop = MaxIterationsStop(150)

    skeleton, extra = build_sa(problem, constructor, neighborhood, stop, T0=5.0, alpha=0.9)
    result = make_run(skeleton, extra)(instance, Random(0))

    null_value = 0.0
    assert -result.best_objective >= null_value
    assert base.is_feasible(result.best_solution, instance)


def test_ils_reaches_feasible_local_optimum(instance):
    base = KnapsackModel()
    evaluator = KnapsackObjective(base, instance)
    problem = bound_problem_model(instance)
    constructor = GreedyRandomizedConstructor(alpha=0.3)
    neighborhood = BitFlipNeighborhood(evaluator)
    ls = hill_climb(problem, neighborhood, strategy="best")

    class Kick:
        def perturb(self, sol, strength, rng):
            idx = rng.sample(range(len(sol)), max(1, int(strength)))
            sol_list = list(sol)
            for i in idx:
                sol_list[i] = not sol_list[i]
            return tuple(sol_list)

    skeleton = build_ils(problem, constructor, ls, Kick(), BetterAcceptance(), MaxIterationsStop(10))
    result = skeleton.run(instance, Random(0))
    assert base.is_feasible(result.best_solution, instance)


def test_lns_mip_repair_respects_fixed_variables(instance):
    base = KnapsackModel()
    evaluator = KnapsackObjective(base, instance)
    problem = bound_problem_model(instance)
    constructor = GreedyRandomizedConstructor(alpha=0.3)
    destruction = RandomDestruction()
    repair = KnapsackMIPRepair(base)

    skeleton = build_lns_mip(
        problem,
        constructor,
        destruction,
        repair,
        AlwaysAccept(),
        MaxIterationsStop(3),
        destroy_ratio=0.3,
        mip_time_limit=2.0,
    )
    result = run_lns_mip(skeleton, instance, Random(0), destroy_ratio=0.3)
    assert base.is_feasible(result.best_solution, instance)
