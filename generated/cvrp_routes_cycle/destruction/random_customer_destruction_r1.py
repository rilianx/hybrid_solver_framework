from __future__ import annotations

from random import Random
from typing import Any

from generated.cvrp_routes_cycle.model.parts import canonical


COMPONENT = {
    "name": "random_customer_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.7]}},
}


class RandomCustomerDestruction:
    """Libera arcos incidentes a un subconjunto aleatorio de clientes."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        sol = canonical(sol)
        assignment = self.problem.to_assignment(sol)
        n = int(self.inst.n_customers)

        customers = list(range(1, n + 1))
        rng.shuffle(customers)
        k = max(1, min(n, int(round(ratio * n))))
        removed = set(customers[:k])

        free_vars: set[str] = set()
        for name in assignment:
            if not name.startswith("x_"):
                continue
            _, i, j = name.split("_")
            if int(i) in removed or int(j) in removed:
                free_vars.add(name)

        if not free_vars:
            c = customers[0]
            for name in assignment:
                if name.startswith(f"x_0_{c}") or name.startswith(f"x_{c}_0"):
                    free_vars.add(name)

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25):
    return RandomCustomerDestruction(problem, problem.inst)
