from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "route_segment_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.from_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class RouteSegmentDestruction:
    """Libera arcos de rutas completas contiguas reconstruidas desde la asignación MIP."""

    def __init__(self, problem, **params):
        self.problem = problem

    def _routes_from_assignment(self, assignment: dict[str, float]) -> list[list[int]]:
        succ: dict[int, int] = {}
        starts: list[int] = []

        for name, val in assignment.items():
            if val <= 0.5 or not name.startswith("x_"):
                continue
            _, i, j = name.split("_")
            i = int(i)
            j = int(j)
            succ[i] = j
            if i == 0 and j != 0:
                starts.append(j)

        routes: list[list[int]] = []
        used: set[int] = set()

        for start in starts:
            if start in used:
                continue
            route: list[int] = []
            cur = start
            while cur != 0 and cur not in used:
                route.append(cur)
                used.add(cur)
                cur = succ.get(cur, 0)
            if route:
                routes.append(route)

        return routes

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = dict(self.problem.to_assignment(sol))
        routes = self._routes_from_assignment(assignment)
        if not routes:
            free = set(rng.sample(list(assignment.keys()), 1))
            partial = {v: val for v, val in assignment.items() if v not in free}
            return partial, free

        route_vars: list[tuple[int, set[str]]] = []
        for r in routes:
            vars_on_route: set[str] = set()
            prev = 0
            if r:
                vars_on_route.add(f"x_0_{r[0]}")
                for c in r:
                    vars_on_route.add(f"x_{prev}_{c}")
                    prev = c
                vars_on_route.add(f"x_{prev}_0")
            route_vars.append((len(vars_on_route), vars_on_route))

        route_vars.sort(key=lambda t: t[0], reverse=True)
        target = max(1, int(round(ratio * len(assignment))))
        chosen: set[str] = set()
        for _, vars_on_route in route_vars:
            if len(chosen) >= target:
                break
            chosen.update(vars_on_route)

        if not chosen:
            chosen = set(rng.sample(list(assignment.keys()), 1))

        partial = {v: val for v, val in assignment.items() if v not in chosen}
        return partial, chosen


def build_component(problem, **params):
    ratio = params.get("ratio", 0.2)
    return RouteSegmentDestruction(problem, ratio=ratio)
