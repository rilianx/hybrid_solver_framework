from __future__ import annotations

from math import atan2, pi
from random import Random
from typing import Any


COMPONENT = {
    "name": "geographic_cluster_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "problem.inst coordinates"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class GeographicClusterDestruction:
    """Libera un sector geográfico contiguo de clientes.

    La destrucción opera sobre un *sector angular* alrededor del depósito:
    se elige un cliente semilla, se toma su ángulo polar y se libera una
    fracción contigua de clientes ordenados por ángulo. Esto produce una
    ruptura geográfica distinta a una destrucción de arcos uniforme y, en
    general, libera clientes que pertenecen a varias rutas a la vez.
    """

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _coord(self, c: int) -> tuple[float, float]:
        x = self.inst.x[c] if hasattr(self.inst, "x") else self.inst.coords[c][0]
        y = self.inst.y[c] if hasattr(self.inst, "y") else self.inst.coords[c][1]
        return float(x), float(y)

    def _depot_coord(self) -> tuple[float, float]:
        dep = getattr(self.inst, "depot", 0)
        return self._coord(int(dep))

    def _polar_angle(self, c: int) -> float:
        dx, dy = self._coord(c)
        ox, oy = self._depot_coord()
        a = atan2(dy - oy, dx - ox)
        if a < 0:
            a += 2.0 * pi
        return a

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = dict(self.problem.to_assignment(sol))
        x_vars = [name for name in assignment if name.startswith("x_")]
        if not x_vars:
            return assignment, set()

        customers = set()
        for name in x_vars:
            parts = name.split("_")
            if len(parts) == 3:
                try:
                    i, j = int(parts[1]), int(parts[2])
                except ValueError:
                    continue
                customers.add(i)
                customers.add(j)

        customers.discard(0)
        if not customers:
            return assignment, set()

        ordered = sorted((self._polar_angle(c), c) for c in customers)
        n = len(ordered)
        target = max(1, int(round(ratio * n)))
        target = min(target, n)

        seed_idx = rng.randrange(n)
        freed_customers = set()
        idx = seed_idx
        while len(freed_customers) < target:
            freed_customers.add(ordered[idx][1])
            idx = (idx + 1) % n
            if idx == seed_idx:
                break

        free_vars = set()
        for name in x_vars:
            parts = name.split("_")
            if len(parts) == 3:
                try:
                    i, j = int(parts[1]), int(parts[2])
                except ValueError:
                    continue
                if i in freed_customers or j in freed_customers:
                    free_vars.add(name)

        if not free_vars:
            free_vars = {rng.choice(x_vars)}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return GeographicClusterDestruction(problem, problem.inst)
