"""Segundo problema (CVRP): los contratos, el validador, el constructor modular y los CLI
genéricos funcionan sin nada específico del CLSP."""

from __future__ import annotations

import json
from random import Random

import pytest

from core.construction import GreedyConstructor
from core.validation import validate_component
from core.validation.semantic_mip import check_problem_model_mip
from examples.cvrp.components import RelocateNeighborhood, SingletonRoutes, TwoOptNeighborhood
from examples.cvrp.construction import CheapestInsertion
from examples.cvrp.problem_model import CVRPInstance, CVRPModel, canonical


@pytest.fixture(scope="module")
def contexts():
    from examples.cvrp.llm_spec import make_contexts

    return make_contexts()


def test_solution_is_canonical_and_round_trips_through_the_mip_view():
    inst = CVRPInstance.random(8, Random(1))
    P = CVRPModel(inst)
    sol = GreedyConstructor(P, CheapestInsertion(P)).build(inst, Random(0))
    assert sol == canonical(sol) and P.is_feasible(sol)
    assert P.from_assignment(P.to_assignment(sol)) == sol
    assert canonical([(3, 4), (), (1, 2)]) == ((1, 2), (3, 4))
    # la penalización hace finito el objetivo de una solución infactible y peor que cualquier factible
    assert P.objective(((1, 2),)) > P.objective(SingletonRoutes().build(inst, Random(0)))


@pytest.mark.parametrize("N", [RelocateNeighborhood, TwoOptNeighborhood])
def test_neighborhood_deltas_are_exact_and_moves_undo(N):
    inst = CVRPInstance.random(9, Random(2), clustered=True)
    P = CVRPModel(inst)
    nbh = N(P)
    for sol in (GreedyConstructor(P, CheapestInsertion(P), rule="rcl", alpha=0.5).build(inst, Random(s)) for s in range(3)):
        for m in list(nbh.moves(sol))[:200]:
            new = nbh.apply(sol, m)
            assert new == canonical(new) and nbh.undo(new, m) == sol
            assert nbh.delta(sol, m) == pytest.approx(P.objective(new) - P.objective(sol), abs=1e-6)


def test_problem_model_passes_the_semantic_mip_layer(contexts):
    for ctx in contexts:
        failed = [r for r in check_problem_model_mip(ctx) if not r.passed]
        assert not failed, [(r.name, r.message) for r in failed]


def test_reference_components_pass_the_validator(contexts):
    from examples.cvrp.catalog import HANDWRITTEN

    ctx = contexts[0]
    for comp, factory in HANDWRITTEN:
        report = validate_component(comp, factory(ctx.problem), ctx)
        if comp["name"] == "two_opt":  # desde una ruta por cliente no tiene movimientos: correcto que no pase como vecindario de partida
            assert report.failed_layer == "contractual"
        else:
            assert report.passed, (comp["name"], report.feedback())


def test_validator_messages_use_the_problem_hints(contexts):
    """El texto del framework es genérico; las sugerencias vienen de `validation_hints`."""
    from core.validation.quality import hint

    P = contexts[0].problem
    assert "2-opt*" in hint(P, "novelty") and "setup" not in hint(P, "novelty")
    assert hint(object(), "novelty") == ""


def test_every_skeleton_runs_on_the_cvrp():
    from examples.cvrp.pack import PACK
    from tuning.cli import make_assembler

    A, _ = make_assembler(PACK, "handwritten")
    inst = PACK.make_instances(1, 5, {"customers": 10})[0]
    P = CVRPModel(inst)
    start = P.objective(SingletonRoutes().build(inst, Random(0)))
    assert set(A.available_skeletons()) == {"SA", "ILS", "LNS_MIP", "FIX_OPT", "TS", "VNS", "GRASP", "LOCAL_BRANCH", "MIP_PERTURB"}
    for sk in A.available_skeletons():
        r = A.assemble(A.default_config(sk))(inst, Random(0), 0.5)
        assert P.is_feasible(r.best_solution) and r.best_objective < start, sk


def test_generic_tuning_cli_runs_on_the_cvrp(tmp_path):
    from examples.cvrp.tune import main

    main(["--catalog", "handwritten", "--size", "8", "--trials", "9", "--budget", "0.2", "--train", "1", "--test", "1",
          "--skeletons", "SA", "ILS", "--out", str(tmp_path)])
    out = json.loads((tmp_path / "handwritten.json").read_text())
    assert out["settings"]["problem"] == "cvrp" and out["settings"]["size"] == "8"
    assert out["test"]["tuned"]["mean"] < 1e9


def test_mip_perturbation_forces_a_change_and_repairs_with_the_mip():
    """Cada patada fija al valor contrario una variable liberada que estaba en 1: el candidato
    nunca es la incumbente, y el sub-MIP lo deja factible."""
    from core.common_components import MaxIterationsStop
    from examples.cvrp.components import RandomRemoval
    from skeletons.mip_perturbation import build_mip_perturbation, run_mip_perturbation

    inst = CVRPInstance.random(9, Random(4))
    P = CVRPModel(inst)
    seen = []

    def no_ls(sol, rng):
        seen.append(sol)
        return sol

    start = GreedyConstructor(P, CheapestInsertion(P))
    sk = build_mip_perturbation(P, start, RandomRemoval(P), no_ls, MaxIterationsStop(6), destroy_ratio=0.4)
    result = run_mip_perturbation(sk, inst, Random(0))
    initial = start.build(inst, Random(0))
    assert seen[0] == initial and len(seen) >= 4
    assert all(s != initial for s in seen[1:2]) and all(P.is_feasible(s) for s in seen[1:])
    assert result.best_objective <= P.objective(initial)


def test_a_component_exception_in_the_quality_layer_is_a_rejection(contexts):
    """CVRP, corrida 17: un vecindario generado lanzaba ValueError en `delta` sobre movimientos
    que la capa contractual no había muestreado, y la excepción tumbaba la generación."""
    from core.validation.pipeline import _quality

    class Flaky(RelocateNeighborhood):
        def delta(self, sol, m):
            raise ValueError("move does not match solution")

    results = _quality("neighborhood", Flaky(contexts[0].problem), contexts[0])
    assert results and not results[0].passed and "ValueError" in results[0].message
