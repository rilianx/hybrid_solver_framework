from __future__ import annotations

COMPONENT = {
    "name": "customer_swap_exchange",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {},
}

from typing import Iterable


class CustomerSwapExchange:
    """Intercambia dos clientes cualesquiera en sus rutas. Movimiento = (a, b)."""

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
                yield (customers[i], customers[j])

    def apply(self, sol, m):
        a, b = m
        sol = self.canonical(sol)
        ra, pa = self._locate(sol, a)
        rb, pb = self._locate(sol, b)

        routes = [list(route) for route in sol]
        routes[ra][pa], routes[rb][pb] = routes[rb][pb], routes[ra][pa]
        return self.canonical(tuple(tuple(r) for r in routes))

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CustomerSwapExchange(problem)
