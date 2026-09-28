from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "related_customer_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class RelatedCustomerDestruction:
    """Libera arcos incidentes a un conjunto de clientes cercanos a un cliente semilla."""

    def __init__(self, problem, **params):
        self.problem = problem

    def _customers_in_solution(self, assignment: dict[str, float]) -> list[int]:
        customers: set[int] = set()
        for name, val in assignment.items():
            if val <= 0.5 or not name.startswith("x_"):
                continue
            _, i, j = name.split("_")
            i = int(i)
            j = int(j)
            if i != 0:
                customers.add(i)
            if j != 0:
                customers.add(j)
        return sorted(customers)

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = dict(self.problem.to_assignment(sol))
        vars_all = list(assignment.keys())
        if not vars_all:
            return {}, set()

        customers = self._customers_in_solution(assignment)
        if not customers:
            free = set(rng.sample(vars_all, 1))
            partial = {v: val for v, val in assignment.items() if v not in free}
            return partial, free

        seed = rng.choice(customers)
        scored = []
        for c in customers:
            if c == seed:
                score = -1.0
            else:
                score = float(self.problem.inst.dist(seed, c))
            scored.append((score, c))
        scored.sort(key=lambda t: t[0])

        target_customers = max(1, int(round(ratio * len(customers))))
        selected_customers = {c for _, c in scored[:target_customers]}

        free: set[str] = set()
        for name, val in assignment.items():
            if val <= 0.5 or not name.startswith("x_"):
                continue
            _, i, j = name.split("_")
            i = int(i)
            j = int(j)
            if i in selected_customers or j in selected_customers:
                free.add(name)

        if not free:
            free = {rng.choice(vars_all)}

        partial = {v: val for v, val in assignment.items() if v not in free}
        return partial, free


def build_component(problem, **params):
    ratio = params.get("ratio", 0.2)
    return RelatedCustomerDestruction(problem, ratio=ratio)
