from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "route_segment_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "Solution canonical routes"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class RouteSegmentDestruction:
    """Libera un segmento contiguo de una ruta completa para reoptimización local."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = dict(self.problem.to_assignment(sol))
        routes = tuple(tuple(int(c) for c in route) for route in sol)
        if not routes:
            x_vars = [name for name in assignment if name.startswith("x_")]
            if not x_vars:
                return assignment, set()
            free_vars = {rng.choice(x_vars)}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        route = rng.choice(routes)
        if not route:
            x_vars = [name for name in assignment if name.startswith("x_")]
            free_vars = {rng.choice(x_vars)}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        m = len(route)
        k = max(1, int(round(ratio * m)))
        if k >= m:
            freed = set(route)
        else:
            start = rng.randrange(0, m - k + 1)
            freed = set(route[start : start + k])

        free_vars = set()
        for c in freed:
            for name in assignment:
                if name == f"x_0_{c}" or name == f"x_{c}_0" or f"_{c}_" in name:
                    if name.startswith("x_"):
                        free_vars.add(name)

        if not free_vars:
            x_vars = [name for name in assignment if name.startswith("x_")]
            free_vars = {rng.choice(x_vars)}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return RouteSegmentDestruction(problem, problem.inst)
