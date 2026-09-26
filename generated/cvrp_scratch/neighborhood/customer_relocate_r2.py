from __future__ import annotations

from typing import Iterable
from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "customer_relocate",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst", "canonical"],
    "params": {},
}


class CustomerRelocateNeighborhood:
    """Reloca un cliente a otro hueco de la solución.

    Movimiento: (c, p, n, a, b)
    - c es el cliente movido
    - p, n son su predecesor y sucesor originales (0 = depósito)
    - a, b identifican el hueco destino entre a y b (0 = depósito)
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def _locate_customer(self, sol, customer):
        for ridx, route in enumerate(sol):
            for i, c in enumerate(route):
                if c == customer:
                    prev_c = route[i - 1] if i > 0 else 0
                    next_c = route[i + 1] if i + 1 < len(route) else 0
                    return ridx, i, prev_c, next_c
        raise ValueError("move does not match solution")

    def _remove_customer(self, routes, customer, prev_c, next_c):
        found = False
        for ridx, route in enumerate(routes):
            for i, c in enumerate(route):
                if c == customer:
                    rp = route[i - 1] if i > 0 else 0
                    rn = route[i + 1] if i + 1 < len(route) else 0
                    if rp != prev_c or rn != next_c:
                        raise ValueError("move does not match solution")
                    new_route = route[:i] + route[i + 1 :]
                    if new_route:
                        routes[ridx] = new_route
                    else:
                        routes.pop(ridx)
                    found = True
                    break
            if found:
                break
        if not found:
            raise ValueError("move does not match solution")
        return routes

    def _insert_customer(self, routes, customer, a, b):
        if a == 0 and b == 0:
            routes.append((customer,))
            return routes

        for ridx, route in enumerate(routes):
            if a == 0:
                if route and route[0] == b:
                    routes[ridx] = (customer,) + route
                    return routes
            else:
                for j in range(len(route) - 1):
                    if route[j] == a and route[j + 1] == b:
                        routes[ridx] = route[: j + 1] + (customer,) + route[j + 1 :]
                        return routes
                if route and route[-1] == a and b == 0:
                    routes[ridx] = route + (customer,)
                    return routes

        raise ValueError("move does not match solution")

    def _relocate(self, sol, c, p, n, a, b):
        routes = [tuple(route) for route in sol]
        ridx, _, cp, cn = self._locate_customer(routes, c)
        if cp != p or cn != n:
            raise ValueError("move does not match solution")
        routes = self._remove_customer(routes, c, p, n)
        routes = self._insert_customer(routes, c, a, b)
        return canonical(routes)

    def moves(self, sol) -> Iterable[tuple]:
        routes = sol
        for route in routes:
            for i, c in enumerate(route):
                p = route[i - 1] if i > 0 else 0
                n = route[i + 1] if i + 1 < len(route) else 0
                # Inserciones en huecos existentes
                for target in routes:
                    if not target:
                        continue
                    yield (c, p, n, 0, target[0])
                    for j in range(len(target) - 1):
                        yield (c, p, n, target[j], target[j + 1])
                    yield (c, p, n, target[-1], 0)
                # Permite crear una ruta singleton nueva
                yield (c, p, n, 0, 0)

    def apply(self, sol, m):
        c, p, n, a, b = m
        return self._relocate(sol, c, p, n, a, b)

    def undo(self, sol, m):
        c, p, n, a, b = m
        return self._relocate(sol, c, a, b, p, n)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CustomerRelocateNeighborhood(problem)
