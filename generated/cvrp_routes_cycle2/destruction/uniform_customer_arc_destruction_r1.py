from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "uniform_customer_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class UniformCustomerArcDestruction:
    """Libera arcos incidentes a clientes elegidos uniformemente al azar."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = dict(self.problem.to_assignment(sol))
        n = int(self.inst.n_customers)
        x_vars = [name for name in assignment if name.startswith("x_")]
        if not x_vars:
            return assignment, set()

        customers = list(range(1, n + 1))
        rng.shuffle(customers)
        target = max(1, int(round(ratio * max(1, n))))

        freed_customers = set(customers[: min(target, n)])
        free_vars = {
            name for name in x_vars if any(name.startswith(f"x_{c}_") or name.endswith(f"_{c}") for c in freed_customers)
        }

        if not free_vars:
            idx = rng.randrange(len(x_vars))
            free_vars = {x_vars[idx]}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return UniformCustomerArcDestruction(problem, problem.inst)
