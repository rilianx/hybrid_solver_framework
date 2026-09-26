COMPONENT = {
    "name": "swap_customers_across_routes",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "canonical"],
    "params": {
        "allow_within_route": {"type": "bool"},
    },
}

from __future__ import annotations

import random
from typing import Iterable

from generated.cvrp_routes_cycle.model.parts import canonical


class SwapCustomersAcrossRoutes:
    """Intercambia dos clientes, posiblemente de rutas distintas.
    Movimiento: (r1, p1, r2, p2).
    """

    def __init__(self, problem, allow_within_route: bool = False):
        self.problem = problem
        self.allow_within_route = bool(allow_within_route)

    def moves(self, sol) -> Iterable[tuple]:
        sol = canonical(sol)
        r = len(sol)
        for i in range(r):
            for p in range(len(sol[i])):
                for j in range(i, r):
                    start_q = p + 1 if i == j else 0
                    for q in range(start_q, len(sol[j])):
                        if i == j and not self.allow_within_route:
                            continue
                        yield (i, p, j, q)

    def apply(self, sol, m):
        sol = canonical(sol)
        i, p, j, q = m
        routes = [list(route) for route in sol]
        if i == j:
            routes[i][p], routes[i][q] = routes[i][q], routes[i][p]
        else:
            a = routes[i][p]
            b = routes[j][q]
            routes[i][p] = b
            routes[j][q] = a
        routes = [tuple(route) for route in routes if route]
        return canonical(tuple(routes))

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, allow_within_route: bool = False):
    return SwapCustomersAcrossRoutes(problem, allow_within_route=allow_within_route)
