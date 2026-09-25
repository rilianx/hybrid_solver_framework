from __future__ import annotations

from typing import Iterable
from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "swap_customers",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "max_candidates": {"type": "int", "range": [1, 50]},
    },
}


class SwapCustomersNeighborhood:
    """Vecindario elemental de intercambio de dos clientes.

    El movimiento intercambia dos clientes distintos. Esto genera vecinos que
    no se obtienen en un solo paso mediante reubicación.
    """

    def __init__(self, problem, max_candidates: int = 20):
        self.problem = problem
        self.max_candidates = max_candidates

    def _as_lists(self, sol):
        return [list(r) for r in sol]

    def _locations(self, sol):
        loc = {}
        for ri, r in enumerate(sol):
            for pi, c in enumerate(r):
                loc[c] = (ri, pi)
        return loc

    def _customer_list(self, sol):
        customers = [c for r in sol for c in r]
        if self.max_candidates > 0:
            customers = customers[: self.max_candidates]
        return customers

    def moves(self, sol) -> Iterable[tuple]:
        customers = self._customer_list(sol)
        n = len(customers)
        for i in range(n):
            a = customers[i]
            for j in range(i + 1, n):
                b = customers[j]
                if a != b:
                    yield (a, b)

    def apply(self, sol, m):
        a, b = m
        routes = self._as_lists(sol)
        loc = self._locations(routes)

        if a not in loc or b not in loc or a == b:
            return canonical(routes)

        ra, ia = loc[a]
        rb, ib = loc[b]

        routes[ra][ia], routes[rb][ib] = routes[rb][ib], routes[ra][ia]
        return canonical(routes)

    def undo(self, sol, m):
        # El intercambio es su propio inverso.
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_candidates: int = 20):
    return SwapCustomersNeighborhood(problem, max_candidates=max_candidates)
