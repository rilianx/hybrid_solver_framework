from __future__ import annotations

COMPONENT = {
    "name": "single_customer_reinsertion",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {},
}

from typing import Iterable
import random


class SingleCustomerReinsertion:
    """Extrae un cliente y lo inserta inmediatamente después de otro. Movimiento = (a, b)."""

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
        for a in customers:
            for b in customers:
                if a != b:
                    yield (a, b)

    def apply(self, sol, m):
        a, b = m
        sol = self.canonical(sol)
        ra, pa = self._locate(sol, a)
        rb, pb = self._locate(sol, b)

        routes = [list(route) for route in sol]
        customer = routes[ra].pop(pa)
        if ra == rb and pa < pb:
            pb -= 1
        routes[rb].insert(pb + 1, customer)

        routes = [tuple(r) for r in routes if r]
        return self.canonical(tuple(routes))

    def undo(self, sol, m):
        a, b = m
        sol = self.canonical(sol)
        rb, pb = self._locate(sol, b)
        ra, pa = self._locate(sol, a)

        routes = [list(route) for route in sol]
        customer = routes[ra].pop(pa)
        if ra == rb and pa > pb:
            pb += 1
        routes[rb].insert(pb, customer)

        routes = [tuple(r) for r in routes if r]
        return self.canonical(tuple(routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return SingleCustomerReinsertion(problem)
