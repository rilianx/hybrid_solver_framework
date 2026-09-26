from __future__ import annotations

from math import atan2
from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "radial_sector_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst", "ProblemModel.variable_groups"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RadialSectorDestruction:
    """Libera un bloque geográfico de clientes cercano en ángulo y distancia al depósito."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        depot = self.inst.coords[0]

        def polar_key(c: int):
            x, y = self.inst.coords[c]
            ang = atan2(y - depot[1], x - depot[0])
            dx, dy = x - depot[0], y - depot[1]
            return (ang, dx * dx + dy * dy)

        customers = sorted(self.inst.customers, key=polar_key)
        n = len(customers)
        k = max(1, min(n, int(round(ratio * n))))
        start = rng.randrange(n)
        block = [customers[(start + t) % n] for t in range(k)]

        free_vars: set[str] = set()
        nodes = set(block)
        for name in assignment:
            _, a, b = name.split("_")
            i, j = int(a), int(b)
            if (i in nodes) or (j in nodes):
                free_vars.add(name)

        if not free_vars:
            c = block[0]
            for j in range(self.inst.n_customers + 1):
                if j != c:
                    free_vars.add(f"x_{c}_{j}")
                    free_vars.add(f"x_{j}_{c}")

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    return RadialSectorDestruction(problem, problem.inst)
