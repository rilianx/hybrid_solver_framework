from __future__ import annotations

COMPONENT = {
    "name": "single_customer_reinsertion",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {},
}

from typing import Iterable


class SingleCustomerReinsertion:
    """Extrae un cliente y lo inserta inmediatamente después de otro.

    Movimiento enriquecido para garantizar undo exacto:
    (a, b, ra, pa, rb, pb), donde (ra, pa) y (rb, pb) son las posiciones
    originales de a y b en la solución sobre la que se generó el movimiento.
    """

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
        sol = self.canonical(sol)
        customers = [c for route in sol for c in route]
        for ra, route_a in enumerate(sol):
            for pa, a in enumerate(route_a):
                for rb, route_b in enumerate(sol):
                    for pb, b in enumerate(route_b):
                        if a != b:
                            yield (a, b, ra, pa, rb, pb)

    def apply(self, sol, m):
        a, b, ra, pa, rb, pb = m
        sol = self.canonical(sol)

        routes = [list(route) for route in sol]

        customer = routes[ra].pop(pa)

        if ra == rb and pa < pb:
            pb -= 1

        routes[rb].insert(pb + 1, customer)

        routes = [tuple(r) for r in routes if r]
        return self.canonical(tuple(routes))

    def undo(self, sol, m):
        a, b, ra, pa, rb, pb = m
        sol = self.canonical(sol)

        routes = [list(route) for route in sol]

        current_r, current_p = self._locate(sol, a)
        customer = routes[current_r].pop(current_p)

        if not routes[current_r]:
            del routes[current_r]
            if current_r < ra:
                ra -= 1

        routes[ra].insert(pa, customer)

        routes = [tuple(r) for r in routes if r]
        return self.canonical(tuple(routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return SingleCustomerReinsertion(problem)
