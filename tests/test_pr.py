"""PR (path relinking) y el slot relink: el esqueleto corre en Python y en C++ y el validador revisa el contrato."""

import pytest
from random import Random

from core.validation.base import ValidationContext
from core.validation.pipeline import validate_component
from examples.jobshop import model_parts as mp
from examples.jobshop.components import OrderRelink
from examples.jobshop.pack import PACK
from tuning.cli import make_assembler

COMP = {"name": "machine_order", "slot": "relink", "compatible_skeletons": ["PR"], "params": {}}


def _ctx():
    inst = PACK.make_instances(1, 5, PACK.parse_size("5x4"))[0]
    return ValidationContext(problem=PACK.problem_factory(inst), instances=[inst], trivial_solutions=[mp.trivial_solution(inst)])


def test_relink_contract():
    ctx = _ctx()
    assert validate_component(COMP, OrderRelink(ctx.problem), ctx).passed

    class Stuck(OrderRelink):
        def step(self, cur, guide, rng):
            return cur

    rep = validate_component(COMP, Stuck(ctx.problem), ctx)
    assert not rep.passed and "relink.path" in rep.feedback()


def test_pr_runs_python_and_native():
    pytest.importorskip("pybind11")
    inst = PACK.make_instances(1, 3, PACK.parse_size("6x5"))[0]
    for native in (False, True):
        A, _ = make_assembler(PACK, "handwritten", None, native=native)
        assert "PR" in A.available_skeletons()
        cfg = A.default_config("PR", {"constructor": "job_order", "neighborhood": "critical_swap", "relink": "machine_order"})
        cfg.update({"PR.pop_size": 4, "PR.ts_iters": 100})
        res = A.assemble(cfg)(inst, Random(0), 0.5)
        assert PACK.problem_factory(inst).is_feasible(res.best_solution)
        assert res.best_objective <= PACK.problem_factory(inst).objective(mp.trivial_solution(inst))


def test_ils_annealing_acceptance_runs_python_and_native():
    pytest.importorskip("pybind11")
    inst = PACK.make_instances(1, 3, PACK.parse_size("6x5"))[0]
    for native in (False, True):
        A, _ = make_assembler(PACK, "handwritten", None, native=native)
        cfg = A.default_config("ILS", {"constructor": "job_order", "neighborhood": "critical_swap"})
        cfg.update({"ILS.accept": "anneal", "ILS.T_rel": 0.01})
        res = A.assemble(cfg)(inst, Random(0), 0.4)
        assert PACK.problem_factory(inst).is_feasible(res.best_solution)


def test_pr_with_ils_improvement_python_and_native():
    pytest.importorskip("pybind11")
    inst = PACK.make_instances(1, 3, PACK.parse_size("6x5"))[0]
    for native in (False, True):
        A, _ = make_assembler(PACK, "handwritten", None, native=native)
        cfg = A.default_config("PR", {"constructor": "job_order", "neighborhood": "critical_swap", "relink": "machine_order",
                                      "perturbation": "critical_kick"})
        cfg.update({"PR.improve": "ils", "PR.pop_size": 4, "PR.ts_iters": 20, "PR.T_rel": 0.01})
        res = A.assemble(cfg)(inst, Random(0), 0.5)
        assert PACK.problem_factory(inst).is_feasible(res.best_solution) and res.iterations > 0


def test_adaptive_penalty_returns_the_best_feasible_solution():
    pytest.importorskip("pybind11")
    """Con un peso bajo de las violaciones la búsqueda pasa por infactibles, pero devuelve la mejor factible."""
    inst = PACK.make_instances(1, 3, PACK.parse_size("6x5"))[0]
    A, _ = make_assembler(PACK, "handwritten", None, native=True)
    for sk, choices in (("TS", {}), ("ILS", {"perturbation": "critical_kick"}), ("SA", {})):
        cfg = A.default_config(sk, {"constructor": "job_order", "neighborhood": "critical_swap", **choices})
        cfg.update({f"{sk}.pen_adapt": "yes", f"{sk}.pen_scale": 1e-4})
        res = A.assemble(cfg)(inst, Random(0), 0.4)
        P = PACK.problem_factory(inst)
        assert P.is_feasible(res.best_solution) and res.best_objective == P.objective(res.best_solution)
