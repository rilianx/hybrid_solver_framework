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
    """Libera rutas completas del gran tour, en lugar de un segmento contiguo del tour."""

    def __init__(self, problem, **params):
        self.problem = problem

    def _assignment_arcs(self, assignment: dict[str, float]) -> dict[int, int]:
        succ: dict[int, int] = {}
        for name, val in assignment.items():
            if val <= 0.5 or not name.startswith("x_"):
                continue
            parts = name.split("_")
            if len(parts) != 3:
                continue
            try:
                i = int(parts[1])
                j = int(parts[2])
            except ValueError:
                continue
            succ[i] = j
        return succ

    def _routes_from_assignment(self, assignment: dict[str, float]) -> list[list[int]]:
        succ = self._assignment_arcs(assignment)
        routes: list[list[int]] = []

        # Walk routes starting from depot outgoing arcs.
        depot_nexts = [j for i, j in succ.items() if i == 0]
        if not depot_nexts:
            return routes

        seen_edges: set[tuple[int, int]] = set()
        for first in depot_nexts:
            route: list[int] = []
            cur = first
            prev = 0
            while True:
                edge = (prev, cur)
                if edge in seen_edges:
                    break
                seen_edges.add(edge)
                if cur == 0:
                    break
                route.append(cur)
                nxt = succ.get(cur, 0)
                prev, cur = cur, nxt
                if cur == 0:
                    seen_edges.add((prev, 0))
                    break
            if route:
                routes.append(route)

        return routes

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = dict(self.problem.to_assignment(sol))
        routes = self._routes_from_assignment(assignment)

        if not routes:
            keys = list(assignment.keys())
            if not keys:
                return assignment, set()
            k = max(1, int(round(ratio * len(keys))))
            k = min(k, len(keys))
            chosen = set(rng.sample(keys, k))
            partial = {v: val for v, val in assignment.items() if v not in chosen}
            return partial, chosen

        # Remove one or several complete routes; this differs structurally from arc/segment destruction.
        n_routes = len(routes)
        k_routes = max(1, int(round(ratio * n_routes)))
        k_routes = min(k_routes, n_routes)

        start = rng.randrange(0, n_routes - k_routes + 1)
        selected_routes = routes[start : start + k_routes]

        freed: set[str] = set()

        selected_nodes = {node for route in selected_routes for node in route}

        # Free every arc entirely contained in the selected route block,
        # plus the depot connections that delimit those routes.
        for name, val in assignment.items():
            if val <= 0.5 or not name.startswith("x_"):
                continue
            parts = name.split("_")
            if len(parts) != 3:
                continue
            try:
                i = int(parts[1])
                j = int(parts[2])
            except ValueError:
                continue

            if i == 0 and j in selected_nodes:
                freed.add(name)
            elif i in selected_nodes and j == 0:
                freed.add(name)
            elif i in selected_nodes and j in selected_nodes:
                freed.add(name)

        if not freed:
            keys = list(assignment.keys())
            k = max(1, int(round(ratio * len(keys))))
            k = min(k, len(keys))
            freed = set(rng.sample(keys, k))

        partial = {v: val for v, val in assignment.items() if v not in freed}
        return partial, freed


def build_component(problem, **params):
    ratio = params.get("ratio", 0.2)
    return RouteSegmentDestruction(problem, ratio=ratio)
