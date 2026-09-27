from __future__ import annotations

from random import Random
from typing import Any

from generated.cvrp_routes_cycle.model.parts import canonical


COMPONENT = {
    "name": "worst_route_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.9]}},
}


class WorstRouteDestruction:
    """Libera la totalidad de una o varias rutas con mayor contribución a distancia."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _route_cost(self, route) -> float:
        prev = 0
        cost = 0.0
        for c in route:
            cost += float(self.inst.dist(prev, c))
            prev = c
        cost += float(self.inst.dist(prev, 0))
        return cost

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        sol = canonical(sol)
        assignment = self.problem.to_assignment(sol)

        routes = list(sol)
        if not routes:
            free_vars = {next(iter(assignment))}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        scored = sorted(
            ((self._route_cost(route), idx, route) for idx, route in enumerate(routes)),
            reverse=True,
        )

        target = max(1, min(len(routes), int(round(ratio * len(routes)))))
        chosen_routes = {idx for _, idx, _ in scored[:target]}

        chosen_customers = set()
        for idx in chosen_routes:
            chosen_customers.update(routes[idx])

        free_vars: set[str] = set()
        for name in assignment:
            if not name.startswith("x_"):
                continue
            _, i, j = name.split("_")
            if int(i) in chosen_customers or int(j) in chosen_customers:
                free_vars.add(name)

        if not free_vars:
            _, idx, route = scored[0]
            chosen_customers = set(route)
            for name in assignment:
                if not name.startswith("x_"):
                    continue
                _, i, j = name.split("_")
                if int(i) in chosen_customers or int(j) in chosen_customers:
                    free_vars.add(name)

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.3):
    return WorstRouteDestruction(problem, problem.inst)
