from __future__ import annotations

from random import Random
from typing import Any


COMPONENT = {
    "name": "shaw_related_customer_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class ShawRelatedCustomerDestruction:
    """Libera clientes relacionados por proximidad geográfica y demanda, favoreciendo reoptimizar una subruta coherente."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        vars_all = set(assignment.keys())
        tour = tuple(int(c) for c in sol)
        n = len(tour)

        k = max(1, int(round(ratio * n)))
        k = min(k, n)

        seed_pos = rng.randrange(n)
        seed = tour[seed_pos]

        def relatedness(c: int) -> float:
            d = self.inst.dist(seed, c)
            dem = abs(float(self.inst.demand[seed]) - float(self.inst.demand[c]))
            return d + 0.1 * dem

        ordered = sorted(tour, key=relatedness)
        chosen_customers = set(ordered[:k])

        free_vars = set()
        for v in vars_all:
            if not v.startswith("x_"):
                continue
            try:
                _, a, b = v.split("_")
                i, j = int(a), int(b)
            except Exception:
                continue
            if i in chosen_customers or j in chosen_customers:
                free_vars.add(v)

        if not free_vars:
            free_vars.add(next(iter(vars_all)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return ShawRelatedCustomerDestruction(problem)
