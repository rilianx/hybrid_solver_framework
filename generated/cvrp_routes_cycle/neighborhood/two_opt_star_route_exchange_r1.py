COMPONENT = {
    "name": "two_opt_star_route_exchange",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "canonical"],
    "params": {
        "allow_empty_side": {"type": "bool"},
    },
}

from __future__ import annotations

import random
from typing import Iterable

from generated.cvrp_routes_cycle.model.parts import canonical


class TwoOptStarRouteExchange:
    """Intercambia sufijos entre dos rutas.
    Movimiento: (r1, p1, r2, p2), donde se intercambian las colas
    route1[p1:] y route2[p2:].
    """

    def __init__(self, problem, allow_empty_side: bool = True):
        self.problem = problem
        self.allow_empty_side = bool(allow_empty_side)

    def moves(self, sol) -> Iterable[tuple]:
        sol = canonical(sol)
        r = len(sol)
        for i in range(r):
            for j in range(i, r):
                li = len(sol[i])
                lj = len(sol[j])
                for p in range(li + 1):
                    for q in range(lj + 1):
                        if i == j:
                            if p >= q:
                                continue
                            if not self.allow_empty_side and (p == 0 or q == li):
                                continue
                        else:
                            if not self.allow_empty_side and (p == 0 and q == 0):
                                continue
                        yield (i, p, j, q)

    def apply(self, sol, m):
        sol = canonical(sol)
        i, p, j, q = m
        routes = [list(route) for route in sol]
        if i == j:
            a = routes[i]
            left = a[:p]
            mid = a[p:q]
            right = a[q:]
            routes[i] = left + list(reversed(mid)) + right
        else:
            ri = routes[i]
            rj = routes[j]
            routes[i] = ri[:p] + rj[q:]
            routes[j] = rj[:q] + ri[p:]
        routes = [tuple(route) for route in routes if route]
        return canonical(tuple(routes))

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, allow_empty_side: bool = True):
    return TwoOptStarRouteExchange(problem, allow_empty_side=allow_empty_side)
