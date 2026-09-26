from __future__ import annotations

from random import Random
from typing import Any


COMPONENT = {
    "name": "route_removal_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.from_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RouteRemovalDestruction:
    """Libera rutas completas seleccionadas en el split implícito del gran tour."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def _routes_from_assignment(self, assignment: dict[str, float]) -> list[list[int]]:
        succ: dict[int, int] = {}
        starts: list[int] = []
        for v, val in assignment.items():
            if not v.startswith("x_") or val <= 0.5:
                continue
            try:
                _, a, b = v.split("_")
                i, j = int(a), int(b)
            except Exception:
                continue
            succ[i] = j
            if i == 0 and j != 0:
                starts.append(j)

        routes: list[list[int]] = []
        used: set[int] = set()

        for s in starts:
            if s in used:
                continue
            route: list[int] = []
            cur = s
            while cur != 0 and cur not in used:
                route.append(cur)
                used.add(cur)
                cur = succ.get(cur, 0)
            if route:
                routes.append(route)

        for c in self.inst.customers:
            if c not in used:
                routes.append([c])

        return routes

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        vars_all = set(assignment.keys())

        routes = self._routes_from_assignment(assignment)
        if not routes:
            free_vars = {next(iter(vars_all))}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        loads = [sum(self.inst.demand[c] for c in r) for r in routes]
        target = max(1, int(round(ratio * len(self.inst.customers))))
        target = min(target, len(self.inst.customers))

        order = list(range(len(routes)))
        rng.shuffle(order)

        chosen_routes: set[int] = set()
        freed = 0
        for idx in order:
            chosen_routes.add(idx)
            freed += len(routes[idx])
            if freed >= target:
                break

        chosen_customers = {c for idx in chosen_routes for c in routes[idx]}

        free_vars = set()
        for v in vars_all:
            if not v.startswith("x_"):
                continue
            try:
                _, a, b = v.split("_")
                i, j = int(a), int(b)
            except Exception:
                continue
            if i in chosen_customers or j in chosen_customers:
                free_vars.add(v)

        if not free_vars:
            free_vars.add(next(iter(vars_all)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return RouteRemovalDestruction(problem)
