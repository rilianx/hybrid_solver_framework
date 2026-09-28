from __future__ import annotations

COMPONENT = {
    "name": "two_opt_star_route_exchange",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "canonical"],
    "params": {
        "allow_empty_side": {"type": "bool"},
    },
}

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
            li = len(sol[i])
            for j in range(i + 1, r):
                lj = len(sol[j])

                for p in range(li + 1):
                    for q in range(lj + 1):
                        # Evita movimientos que eliminen una ruta completa,
                        # porque la representación canónica omite rutas vacías
                        # y eso rompería undo(...).
                        if not self.allow_empty_side:
                            if (p == li and q == 0) or (p == 0 and q == lj):
                                continue
                        else:
                            if (p == li and q == 0) or (p == 0 and q == lj):
                                continue
                        yield (i, p, j, q)

    def apply(self, sol, m):
        sol = canonical(sol)
        i, p, j, q = m
        routes = [list(route) for route in sol]

        ri = routes[i]
        rj = routes[j]

        new_ri = ri[:p] + rj[q:]
        new_rj = rj[:q] + ri[p:]

        # Mantener el número de rutas para que undo sea exacto.
        routes[i] = new_ri
        routes[j] = new_rj
        return tuple(tuple(route) for route in routes)

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, allow_empty_side: bool = True):
    return TwoOptStarRouteExchange(problem, allow_empty_side=allow_empty_side)
