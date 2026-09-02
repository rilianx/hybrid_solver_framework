"""Integración del piloto CLSP: puente heurístico↔MIP, Relax-and-Fix,
Fix-and-Optimize y el híbrido Relax-and-Fix → Fix-and-Optimize (§5.2)."""

from random import Random

import pytest

pytest.importorskip("pulp")

from core.common_components import AlwaysAccept, BetterAcceptance, MIPModelRepair, MaxIterationsStop
from core.contracts import ProblemModel
from core.fixing_policies import SlidingWindowPolicy
from core.mip import MIPModel
from examples.lotsizing.components import LotForLotConstructor, PeriodWindowDestruction, SetupFlipNeighborhood
from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel
from skeletons.fix_and_optimize import build_fix_and_optimize, run_fix_and_optimize
from skeletons.lns_mip import build_lns_mip, run_lns_mip
from skeletons.relax_and_fix import RelaxAndFixConstructor


@pytest.fixture(scope="module")
def problem():
    inst = CLSPInstance.random(3, 5, Random(11))
    return LotSizingModel(inst)


def test_problem_model_satisfies_protocols(problem):
    assert isinstance(problem, ProblemModel)
    assert isinstance(problem.build_mip(problem.inst), MIPModel)


def test_assignment_round_trip(problem):
    sol = LotForLotConstructor().build(problem.inst, Random(0))
    assert problem.from_assignment(problem.to_assignment(sol)) == sol


def test_variable_groups_are_periods_and_cover_all_mip_variables(problem):
    groups = problem.variable_groups(problem.inst)
    assert len(groups) == problem.inst.n_periods
    assert {v for vs in groups.values() for v in vs} == set(problem.mip.variables())


def test_cross_validation_heuristic_vs_mip_objective(problem):
    """Capa 3 de §7: fijar la solución en el MIP debe reproducir el objetivo heurístico."""
    sol = LotForLotConstructor().build(problem.inst, Random(0))
    x = problem.mip.solve(fixed=problem.to_assignment(sol), integer=set(), relaxed=set(), time_limit=5)
    assert problem.from_assignment(x) == sol
    assert problem.objective(problem.from_assignment(x)) == pytest.approx(problem.objective(sol))


def test_neighborhood_undo_apply_identity_and_delta_consistency(problem):
    nbh = SetupFlipNeighborhood(problem)
    sol = LotForLotConstructor().build(problem.inst, Random(0))
    for m in list(nbh.moves(sol))[:4]:
        applied = nbh.apply(sol, m)
        assert nbh.undo(applied, m) == sol
        assert nbh.delta(sol, m) == pytest.approx(problem.objective(applied) - problem.objective(sol))


def test_relax_and_fix_builds_feasible_solution_not_worse_than_lot_for_lot(problem):
    lfl = LotForLotConstructor()
    rf = RelaxAndFixConstructor(problem, SlidingWindowPolicy(2, 1), time_limit_per_window=5, fallback=lfl)
    sol = rf.build(problem.inst, Random(0))
    assert rf.last_failed_window is None
    assert problem.is_feasible(sol)
    assert problem.objective(sol) <= problem.objective(lfl.build(problem.inst, Random(0))) + 1e-6


def test_fix_and_optimize_never_worsens_with_better_acceptance(problem):
    rf = RelaxAndFixConstructor(problem, SlidingWindowPolicy(2, 1), 5, fallback=LotForLotConstructor())
    start_cost = problem.objective(rf.build(problem.inst, Random(0)))
    fo = build_fix_and_optimize(problem, rf, SlidingWindowPolicy(2, 1), BetterAcceptance(), MaxIterationsStop(4), block_size=2, time_limit=5)
    result = run_fix_and_optimize(fo, problem.inst, Random(0))
    assert result.best_objective <= start_cost + 1e-6
    assert problem.is_feasible(result.best_solution)


def test_lns_mip_with_period_window_destruction(problem):
    lns = build_lns_mip(
        problem, LotForLotConstructor(), PeriodWindowDestruction(problem.inst), MIPModelRepair(problem),
        AlwaysAccept(), MaxIterationsStop(3), destroy_ratio=0.5, mip_time_limit=5,
    )
    result = run_lns_mip(lns, problem.inst, Random(0), destroy_ratio=0.5)
    assert problem.is_feasible(result.best_solution)


def test_matheuristics_reach_full_mip_optimum_on_small_instance(problem):
    x = problem.mip.solve(fixed={}, integer=set(problem.mip.variables()), relaxed=set(), time_limit=20)
    opt = problem.objective(problem.from_assignment(x))
    rf = RelaxAndFixConstructor(problem, SlidingWindowPolicy(2, 1), 5, fallback=LotForLotConstructor())
    fo = build_fix_and_optimize(problem, rf, SlidingWindowPolicy(2, 1), BetterAcceptance(), MaxIterationsStop(6), block_size=2, time_limit=5)
    result = run_fix_and_optimize(fo, problem.inst, Random(0))
    assert result.best_objective == pytest.approx(opt, rel=0.02)
