from __future__ import annotations

from math import hypot
from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "random_customer_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RandomCustomerArcDestruction:
    """Libera arcos incidentes a un subconjunto aleatorio de clientes."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        customers = list(self.inst.customers)
        n = len(customers)
        k = max(1, min(n, int(round(ratio * n))))
        chosen = set(rng.sample(customers, k))

        free_vars = {
            name
            for name in assignment
            if any(name == f"x_{i}_{j}" for i in chosen for j in range(self.inst.n_customers + 1) if i != j)
            or any(name == f"x_{j}_{i}" for i in chosen for j in range(self.inst.n_customers + 1) if i != j)
        }
        if not free_vars:
            c = rng.choice(customers)
            for j in range(self.inst.n_customers + 1):
                if j != c:
                    free_vars.add(f"x_{c}_{j}")
                    free_vars.add(f"x_{j}_{c}")

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    return RandomCustomerArcDestruction(problem, problem.inst)
