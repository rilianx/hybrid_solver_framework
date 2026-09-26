from __future__ import annotations

from random import Random
from typing import Any


COMPONENT = {
    "name": "random_customer_block_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RandomCustomerBlockDestruction:
    """Libera un bloque contiguo de clientes del gran tour, junto con sus arcos incidentes."""

    def __init__(self, problem):
        self.problem = problem

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        vars_all = set(assignment.keys())
        tour = tuple(int(c) for c in sol)
        n = len(tour)

        k = max(1, int(round(ratio * n)))
        k = min(k, n)

        start = rng.randrange(n)
        block_pos = {(start + i) % n for i in range(k)}
        block_customers = {tour[i] for i in block_pos}

        free_vars = set()
        for v in vars_all:
            if not v.startswith("x_"):
                continue
            try:
                _, a, b = v.split("_")
                i, j = int(a), int(b)
            except Exception:
                continue
            if i in block_customers or j in block_customers:
                free_vars.add(v)

        if not free_vars:
            free_vars.add(next(iter(vars_all)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return RandomCustomerBlockDestruction(problem)
