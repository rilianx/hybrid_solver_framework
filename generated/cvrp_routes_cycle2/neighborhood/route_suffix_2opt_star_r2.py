from __future__ import annotations

COMPONENT = {
    "name": "route_suffix_2opt_star",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {},
}

from typing import Iterable
import random


class RouteSuffix2OptStar:
    """Intercambia los sufijos posteriores a dos clientes. Movimiento = (a, b)."""

    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def _locate(self, sol, customer: int):
        for r_idx, route in enumerate(sol):
            for p_idx, c in enumerate(route):
                if c == customer:
                    return r_idx, p_idx
        raise ValueError("customer not found")

    def moves(self, sol) -> Iterable[tuple]:
        customers = [c for route in sol for c in route]
        n = len(customers)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = customers[i], customers[j]
                ra, _ = self._locate(sol, a)
                rb, _ = self._locate(sol, b)
                if ra != rb or a != b:
                    yield (a, b)

    def apply(self, sol, m):
        a, b = m
        sol = self.canonical(sol)
        ra, pa = self._locate(sol, a)
        rb, pb = self._locate(sol, b)

        routes = [list(route) for route in sol]
        if ra == rb:
            if pa == pb:
                return sol
            i, j = sorted((pa, pb))
            routes[ra][i + 1 : j + 1] = reversed(routes[ra][i + 1 : j + 1])
        else:
            tail_a = routes[ra][pa + 1 :]
            tail_b = routes[rb][pb + 1 :]
            routes[ra] = routes[ra][: pa + 1] + tail_b
            routes[rb] = routes[rb][: pb + 1] + tail_a

        routes = [tuple(r) for r in routes if r]
        return self.canonical(tuple(routes))

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return RouteSuffix2OptStar(problem)
