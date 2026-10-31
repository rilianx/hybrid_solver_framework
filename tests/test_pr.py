"""PR (path relinking) y el slot relink: el esqueleto corre en Python y en C++ y el validador revisa el contrato."""

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
    inst = PACK.make_instances(1, 3, PACK.parse_size("6x5"))[0]
    for native in (False, True):
        A, _ = make_assembler(PACK, "handwritten", None, native=native)
        assert "PR" in A.available_skeletons()
        cfg = A.default_config("PR", {"constructor": "job_order", "neighborhood": "critical_swap", "relink": "machine_order"})
        cfg.update({"PR.pop_size": 4, "PR.ts_iters": 100})
        res = A.assemble(cfg)(inst, Random(0), 0.5)
        assert PACK.problem_factory(inst).is_feasible(res.best_solution)
        assert res.best_objective <= PACK.problem_factory(inst).objective(mp.trivial_solution(inst))
