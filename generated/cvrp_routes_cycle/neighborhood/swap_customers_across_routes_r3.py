from __future__ import annotations

COMPONENT = {
    "name": "swap_customers_across_routes",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "canonical"],
    "params": {
        "allow_within_route": {"type": "bool"},
    },
}

from typing import Iterable

from generated.cvrp_routes_cycle.model.parts import canonical


class SwapCustomersAcrossRoutes:
    """Intercambia dos clientes por identidad.

    El movimiento se representa como (a, b), donde a y b son clientes.
    Si los clientes están en rutas distintas, se intercambian entre rutas.
    Si están en la misma ruta, se intercambian sus posiciones dentro de la ruta
    solo si allow_within_route es True.
    """

    def __init__(self, problem, allow_within_route: bool = False):
        self.problem = problem
        self.allow_within_route = bool(allow_within_route)

    def _find_customer(self, sol, customer):
        for i, route in enumerate(sol):
            for p, c in enumerate(route):
                if c == customer:
                    return i, p
        raise ValueError(f"customer {customer} not found in solution")

    def moves(self, sol) -> Iterable[tuple]:
        sol = canonical(sol)
        customers = [c for route in sol for c in route]
        n = len(customers)
        for i in range(n):
            for j in range(i + 1, n):
                a = customers[i]
                b = customers[j]
                if not self.allow_within_route:
                    ra, _ = self._find_customer(sol, a)
                    rb, _ = self._find_customer(sol, b)
                    if ra == rb:
                        continue
                yield (a, b)

    def apply(self, sol, m):
        sol = canonical(sol)
        a, b = m
        ra, pa = self._find_customer(sol, a)
        rb, pb = self._find_customer(sol, b)

        routes = [list(route) for route in sol]
        routes[ra][pa], routes[rb][pb] = routes[rb][pb], routes[ra][pa]
        routes = [tuple(route) for route in routes if route]
        return canonical(tuple(routes))

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, allow_within_route: bool = False):
    return SwapCustomersAcrossRoutes(problem, allow_within_route=allow_within_route)
