from __future__ import annotations

COMPONENT = {
    "name": "relocate_customer_between_routes",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "canonical"],
    "params": {
        "same_route_allowed": {"type": "bool"},
    },
}

import random
from typing import Iterable

from generated.cvrp_routes_cycle.model.parts import canonical


class RelocateCustomerBetweenRoutes:
    """Mueve un cliente a otra posición, dentro de su ruta o entre rutas.
    Movimiento: (src_route, src_pos, dst_route, dst_pos).
    """

    def __init__(self, problem, same_route_allowed: bool = True):
        self.problem = problem
        self.same_route_allowed = bool(same_route_allowed)

    def moves(self, sol) -> Iterable[tuple]:
        sol = canonical(sol)
        r = len(sol)
        for i, route in enumerate(sol):
            for p in range(len(route)):
                for j in range(r):
                    if i == j and not self.same_route_allowed:
                        continue
                    max_ins = len(sol[j]) if j != i else len(sol[j]) - 1
                    for q in range(max_ins + 1):
                        if i == j and q == p:
                            continue
                        yield (i, p, j, q)

    def apply(self, sol, m):
        sol = canonical(sol)
        i, p, j, q = m
        routes = [list(route) for route in sol]
        c = routes[i].pop(p)
        if i == j and q > p:
            q -= 1
        routes[j].insert(q, c)
        routes = [tuple(route) for route in routes if route]
        return canonical(tuple(routes))

    def undo(self, sol, m):
        sol = canonical(sol)
        i, p, j, q = m
        routes = [list(route) for route in sol]
        if i == j:
            c = routes[j].pop(q)
            if p > q:
                p -= 1
            routes[i].insert(p, c)
        else:
            c = routes[j].pop(q)
            routes[i].insert(p, c)
        routes = [tuple(route) for route in routes if route]
        return canonical(tuple(routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, same_route_allowed: bool = True):
    return RelocateCustomerBetweenRoutes(problem, same_route_allowed=same_route_allowed)
