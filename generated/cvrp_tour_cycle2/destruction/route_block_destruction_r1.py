from random import Random
from typing import Any

COMPONENT = {
    "name": "route_block_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RouteBlockDestruction:
    """Libera rutas completas seleccionadas por coste total, rompiendo bloques enteros del gran tour."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _routes_from_assignment(self, assignment: dict[str, float]) -> list[list[int]]:
        succ: dict[int, int] = {}
        starts: list[int] = []
        for var, val in assignment.items():
            if not var.startswith("x_") or val <= 0.5:
                continue
            _, i, j = var.split("_")
            ii, jj = int(i), int(j)
            succ[ii] = jj
            if ii == 0 and jj != 0:
                starts.append(jj)

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

    def _route_cost(self, route: list[int]) -> float:
        if not route:
            return 0.0
        total = self.inst.dist(0, route[0])
        for a, b in zip(route, route[1:]):
            total += self.inst.dist(a, b)
        total += self.inst.dist(route[-1], 0)
        return total

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        routes = self._routes_from_assignment(assignment)
        if not routes:
            free_vars = {next(v for v in assignment if v.startswith("x_"))}
            return {v: val for v, val in assignment.items() if v not in free_vars}, free_vars

        scored = [(self._route_cost(route), idx) for idx, route in enumerate(routes)]
        scored.sort(reverse=True)

        k = max(1, int(round(ratio * len(routes))))
        k = min(k, len(routes))
        chosen_routes = {idx for _, idx in scored[:k]}

        chosen_customers: set[int] = set()
        for idx in chosen_routes:
            chosen_customers.update(routes[idx])

        free_vars: set[str] = set()
        for var in assignment:
            if not var.startswith("x_"):
                continue
            _, i, j = var.split("_")
            ii, jj = int(i), int(j)
            if ii in chosen_customers or jj in chosen_customers:
                free_vars.add(var)

        if not free_vars:
            for var in assignment:
                if var.startswith("x_"):
                    free_vars.add(var)
                    break

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = float(params.get("ratio", 0.2))
    return RouteBlockDestruction(problem, problem.inst)
