from __future__ import annotations

from math import hypot
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
    """Libera clientes cercanos a un cliente semilla, formando un clúster geográfico."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _coord(self, c: int) -> tuple[float, float]:
        x = self.inst.x[c] if hasattr(self.inst, "x") else self.inst.coords[c][0]
        y = self.inst.y[c] if hasattr(self.inst, "y") else self.inst.coords[c][1]
        return float(x), float(y)

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = dict(self.problem.to_assignment(sol))
        x_vars = [name for name in assignment if name.startswith("x_")]
        n = int(self.inst.n_customers)
        if not x_vars or n <= 0:
            return assignment, set()

        seed = rng.randrange(1, n + 1)
        sx, sy = self._coord(seed)

        dist_list = []
        for c in range(1, n + 1):
            cx, cy = self._coord(c)
            dist_list.append((hypot(cx - sx, cy - sy), c))
        dist_list.sort()

        k = max(1, int(round(ratio * n)))
        freed = {c for _, c in dist_list[:k]}

        free_vars = set()
        for name in x_vars:
            parts = name.split("_")
            if len(parts) == 3:
                i, j = int(parts[1]), int(parts[2])
                if i in freed or j in freed:
                    free_vars.add(name)

        if not free_vars:
            free_vars = {rng.choice(x_vars)}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return GeographicClusterDestruction(problem, problem.inst)
