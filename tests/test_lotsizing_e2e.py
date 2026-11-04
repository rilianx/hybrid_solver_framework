"""Integración del piloto CLSP: puente heurístico↔MIP y el sub-MIP de HYB (destrucción + reparación)."""

from random import Random

import pytest

pytest.importorskip("pulp")

from core.common_components import MIPModelRepair
from core.mip import MIPModel
from core.packs import GroupWindowDestruction
from examples.lotsizing.instance import CLSPInstance
from tests.clsp_fixtures import LotForLotConstructor, LotSizingModel, SetupFlipNeighborhood


@pytest.fixture(scope="module")
def problem():
    inst = CLSPInstance.random(3, 5, Random(11))
    return LotSizingModel(inst)


def test_the_mip_view_is_a_mip_model(problem):
    assert isinstance(problem.build_mip(problem.inst), MIPModel)


def test_assignment_round_trip(problem):
    sol = LotForLotConstructor().build(problem.inst, Random(0))
    assert problem.from_assignment(problem.to_assignment(sol)) == sol


def test_variable_groups_are_periods_and_cover_all_mip_variables(problem):
    groups = problem.variable_groups(problem.inst)
    assert len(groups) == problem.inst.n_periods
    assert {v for vs in groups.values() for v in vs} == set(problem.build_mip(problem.inst).variables())


def test_cross_validation_heuristic_vs_mip_objective(problem):
    """Capa 3 de §7: fijar la solución en el MIP debe reproducir el objetivo heurístico."""
    sol = LotForLotConstructor().build(problem.inst, Random(0))
    x = problem.build_mip(problem.inst).solve(fixed=problem.to_assignment(sol), integer=set(), relaxed=set(), time_limit=5)
    assert problem.from_assignment(x) == sol
    assert problem.objective(problem.from_assignment(x)) == pytest.approx(problem.objective(sol))


def test_neighborhood_undo_apply_identity_and_delta_consistency(problem):
    nbh = SetupFlipNeighborhood(problem)
    sol = LotForLotConstructor().build(problem.inst, Random(0))
    for m in list(nbh.moves(sol))[:4]:
        applied = nbh.apply(sol, m)
        assert nbh.undo(applied, m) == sol
        assert nbh.delta(sol, m) == pytest.approx(problem.objective(applied) - problem.objective(sol))


def test_destruction_and_mip_repair_never_worsen_a_feasible_solution(problem):
    """El paso de sub-MIP de HYB: liberar una ventana de períodos y resolver el resto fijo, con la incumbente de
    partida."""
    sol = LotForLotConstructor().build(problem.inst, Random(0))
    assert problem.is_feasible(sol)
    destr, repair, mip = GroupWindowDestruction(problem), MIPModelRepair(problem), problem.build_mip(problem.inst)
    rng = Random(0)
    for _ in range(3):
        _partial, free = destr.destroy(sol, 0.5, rng)
        full = problem.to_assignment(sol)
        cand = repair.repair_mip(mip, {v: x for v, x in full.items() if v not in free}, free, time_limit=5, warm_start=full)
        assert cand is not None and problem.is_feasible(cand)
        assert problem.objective(cand) <= problem.objective(sol) + 1e-6
        sol = cand


def test_hybrid_reaches_the_full_mip_optimum_on_a_small_instance(problem):
    from core.assembler import Assembler
    from tests.clsp_fixtures import clsp_registry

    x = problem.build_mip(problem.inst).solve(fixed={}, integer=set(problem.build_mip(problem.inst).variables()), relaxed=set(), time_limit=20)
    opt = problem.objective(problem.from_assignment(x))
    A = Assembler(problem_factory=LotSizingModel, registry=clsp_registry())
    cfg = A.default_config("HYB", {"constructor": "lot_for_lot", "destruction": "period_window"})
    cfg["HYB.destroy_ratio"] = 0.6
    result = A.assemble(cfg)(problem.inst, Random(0), 3.0)
    assert problem.is_feasible(result.best_solution)
    assert result.best_objective == pytest.approx(opt, rel=0.02)
