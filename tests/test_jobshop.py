"""Tercer problema (job shop, makespan): entra directamente por piezas. Las piezas de referencia de
sus dos representaciones pasan el validador de modelos con los casos, y el catálogo escrito a mano
pasa el validador de componentes y corre en todos los esqueletos."""

from __future__ import annotations

from random import Random

import pytest

from core.model_parts import PartsModel
from core.validation import validate_component
from core.validation.model_parts import check_construction_view, validate_parts
from examples.jobshop import model_parts, ops_parts
from examples.jobshop.cases import brute_force_optimum, load_cases
from examples.jobshop.components import CriticalInsert, CriticalSwap
from examples.jobshop.instance import JSSPInstance


@pytest.fixture(scope="module")
def pack():
    from examples.jobshop.pack import PACK

    return PACK


def test_the_instance_text_round_trips():
    inst = JSSPInstance.random(4, 3, Random(1))
    assert JSSPInstance.parse(inst.to_text()) == inst
    assert sorted(m for m, _ in inst.routes[0]) == [0, 1, 2]


def test_a_cycle_is_an_order_violation_and_a_missing_job_a_sequence_violation():
    inst = JSSPInstance(((( 0, 2), (1, 3)), ((1, 2), (0, 3))), 2)  # trabajo 0: m0 -> m1; trabajo 1: m1 -> m0
    assert model_parts.violations(inst, ((0, 1), (1, 0))) == {"secuencia": 0.0, "orden": 0.0}
    assert model_parts.cost_terms(inst, ((0, 1), (1, 0)))["makespan"] == 5.0
    assert model_parts.violations(inst, ((1, 0), (0, 1)))["orden"] > 0  # 1 antes que 0 en m0 y 0 antes que 1 en m1
    assert model_parts.violations(inst, ((0,), (1, 0)))["secuencia"] == 1.0


@pytest.mark.parametrize("parts,decoder", [(model_parts, False), (ops_parts, True)])
def test_the_reference_parts_pass_the_model_validator(parts, decoder):
    cases = load_cases()
    scale = [JSSPInstance.random(10, 10, Random(777))]
    report = validate_parts(parts, cases, scale_instances=scale, decoder=decoder)
    assert report.passed, report.feedback()
    report = check_construction_view(parts, cases, scale_instances=scale)
    assert report.passed, report.feedback()


def test_the_cases_optimum_is_the_brute_force_one():
    case = load_cases()[0]
    assert brute_force_optimum(case.instance)[0] == case.optimum
    assert min(s["cost"] for s in case.solutions if s["feasible"]) == case.optimum


@pytest.mark.parametrize("N", [CriticalSwap, CriticalInsert])
def test_critical_moves_undo_and_swaps_never_create_a_cycle(N):
    inst = JSSPInstance.random(6, 4, Random(3))
    P = PartsModel(model_parts, inst)
    nbh = N(P)
    for s in range(3):
        sol = model_parts.random_solution(inst, Random(s))
        moves = list(nbh.moves(sol))
        assert moves
        for m in moves:
            new = nbh.apply(sol, m)
            assert nbh.undo(new, m) == sol
            assert nbh.delta(sol, m) == pytest.approx(P.objective(new) - P.objective(sol))
            if N is CriticalSwap:
                assert P.is_feasible(new)


def test_the_handwritten_components_pass_the_validator(pack):
    ctx = pack.make_contexts()[0]
    failed = {}
    for comp, factory in pack.handwritten:
        if comp["slot"] in ("greedy_score", "fixing_policy"):
            continue
        report = validate_component(comp, factory(ctx.problem), ctx)
        if not report.passed:
            failed[comp["name"]] = report.feedback()
    assert not failed, failed


def test_every_skeleton_runs_on_the_job_shop(pack):
    from tuning.cli import make_assembler

    A, _ = make_assembler(pack, "handwritten")
    inst = pack.make_instances(1, 5, pack.parse_size("6x4"))[0]
    P = pack.problem_factory(inst)
    start = P.objective(pack.baseline_constructor().build(inst, Random(0)))
    for sk in A.available_skeletons():
        r = A.assemble(A.default_config(sk))(inst, Random(0), 0.5)
        assert P.is_feasible(r.best_solution) and r.best_objective <= start, sk


def test_the_cycle_loads_both_job_shop_variants():
    from llm.cycle import load_variant

    for variant in ("sequences", "operations"):
        pack = load_variant("jobshop", variant, None, reference=True)
        inst = pack.make_instances(1, 1, pack.parse_size(pack.default_size))[0]
        P = pack.problem_factory(inst)
        assert P.is_feasible(pack.baseline_constructor().build(inst, Random(0)))
