from __future__ import annotations

import math
from random import Random
from typing import Any

from examples.cvrp.problem_model import var_name

COMPONENT = {
    "name": "radial_sector_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RadialSectorDestruction:
    """Libera un sector angular contiguo de clientes cercanos geográficamente al mismo 'ángulo'."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        customers = list(self.inst.customers)
        if not customers:
            return assignment, {next(iter(assignment))}

        angles = {
            c: math.atan2(self.inst.coords[c][1] - self.inst.coords[0][1], self.inst.coords[c][0] - self.inst.coords[0][0])
            for c in customers
        }
        ordered = sorted(customers, key=lambda c: angles[c])
        k = max(1, int(round(ratio * len(ordered))))
        start = rng.randrange(len(ordered))
        chosen = {ordered[(start + t) % len(ordered)] for t in range(k)}

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
    return RadialSectorDestruction(problem, problem.inst)
