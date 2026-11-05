"""Job shop (makespan): la instancia, los casos y las piezas de referencia en Python (el modelo C++ y los componentes
generados se prueban en `tests/test_native.py`)."""

from __future__ import annotations

from random import Random

import pytest

from core.validation.model_parts import validate_parts
from examples.jobshop import model_parts
from examples.jobshop.cases import brute_force_optimum, load_cases
from examples.jobshop.instance import JSSPInstance


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


def test_the_reference_parts_pass_the_model_validator():
    cases = load_cases()
    scale = [JSSPInstance.random(10, 10, Random(777))]
    from tests.mip_views import full_parts

    report = validate_parts(full_parts("jobshop"), cases, scale_instances=scale)  # el oráculo con la vista MIP generada
    assert report.passed, report.feedback()


def test_the_cases_optimum_is_the_brute_force_one():
    case = load_cases()[0]
    assert brute_force_optimum(case.instance)[0] == case.optimum
    assert min(s["cost"] for s in case.solutions if s["feasible"]) == case.optimum


def test_the_taillard_instances_load_and_have_a_published_best_known():
    from scripts.bench_eval import BENCHES

    TAILLARD, bk = BENCHES["jobshop"].dir, BENCHES["jobshop"].reference()
    for i in range(1, 21):
        inst = JSSPInstance.load(str(TAILLARD / f"ta{i:02d}.txt"))
        assert (inst.n_jobs, inst.n_machines) == ((15, 15) if i <= 10 else (20, 15))
        assert all(sorted(m for m, _ in r) == list(range(inst.n_machines)) for r in inst.routes)
        # el mejor conocido es alcanzable: no menor que la cota trivial (la máquina o el trabajo más cargado)
        lb = max(max(sum(p for _, p in r) for r in inst.routes),
                 max(sum(p for r in inst.routes for m, p in r if m == mm) for mm in inst.machines))
        assert bk[f"ta{i:02d}"] >= lb
