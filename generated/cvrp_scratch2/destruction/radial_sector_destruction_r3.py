from __future__ import annotations

import math
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
    """Libera clientes en un sector radial y todas sus variables incidentes."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        customers = list(self.inst.customers)
        n = len(customers)
        if n == 0:
            return assignment, set()

        # Orden angular estable para formar un sector radial.
        depot_x, depot_y = self.inst.coords[0]
        ordered = []
        for c in customers:
            x, y = self.inst.coords[c]
            ang = math.atan2(y - depot_y, x - depot_x)
            ordered.append((ang, c))
        ordered.sort()
        ordered_customers = [c for _, c in ordered]

        # Tamaño monótono con ratio: más ratio => no menos clientes liberados.
        k = max(1, min(n, int(math.ceil(ratio * n))))

        start = rng.randrange(n)
        removed = {
            ordered_customers[(start + t) % n]
            for t in range(k)
        }

        free_vars: set[str] = set()
        for name in assignment:
            if not name.startswith("x_"):
                continue
            _, a, b = name.split("_")
            i, j = int(a), int(b)
            if i in removed or j in removed:
                free_vars.add(name)

        # Fallback seguro: si por alguna razón no se libera nada, liberar un cliente.
        if not free_vars:
            c = ordered_customers[start]
            for j in range(self.inst.n_customers + 1):
                if j != c:
                    free_vars.add(f"x_{c}_{j}")
                    free_vars.add(f"x_{j}_{c}")

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    return RadialSectorDestruction(problem, problem.inst)
