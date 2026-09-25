from __future__ import annotations

from random import Random
from typing import Any

from examples.cvrp.problem_model import var_name

COMPONENT = {
    "name": "random_customer_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RandomCustomerDestruction:
    """Libera clientes al azar y todos los arcos incidentes a ellos."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        customers = [c for route in sol for c in route]
        if not customers:
            return assignment, {var_name(0, 0)} if False else {next(iter(assignment))}
        k = max(1, int(round(ratio * len(customers))))
        chosen = set(rng.sample(customers, min(k, len(customers))))
        free_vars = set()
        for name in assignment:
            _, a, b = name.split("_")
            i, j = int(a), int(b)
            if i in chosen or j in chosen:
                free_vars.add(name)
        if not free_vars:
            free_vars.add(next(iter(assignment)))
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = params.get("ratio", 0.25)
    return RandomCustomerDestruction(problem, problem.inst)
