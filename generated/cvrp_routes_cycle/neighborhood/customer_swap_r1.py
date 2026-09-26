from __future__ import annotations

from random import Random
from typing import Iterable

from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "customer_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "allow_intra_route": {"type": "bool", "values": [True, False]},
    },
}


class CustomerSwapNeighborhood:
    """Intercambia dos clientes. Movimiento = (ri, pi, rj, pj)."""

    def __init__(self, problem, allow_intra_route: bool = True):
        self.problem = problem
        self.allow_intra_route = bool(allow_intra_route)

    def moves(self, sol) -> Iterable[tuple]:
        sol = canonical(sol)
        for ri, route in enumerate(sol):
            for pi in range(len(route)):
                start_rj = ri if self.allow_intra_route else ri + 1
                for rj in range(start_rj, len(sol)):
                    route2 = sol[rj]
                    pj0 = pi + 1 if rj == ri else 0
                    for pj in range(pj0, len(route2)):
                        if ri == rj and pi == pj:
                            continue
                        yield (ri, pi, rj, pj)

    def apply(self, sol, m):
        ri, pi, rj, pj = m
        sol = canonical(sol)
        routes = [list(r) for r in sol]
        a = routes[ri][pi]
        b = routes[rj][pj]
        routes[ri][pi] = b
        routes[rj][pj] = a
        return canonical(tuple(tuple(r) for r in routes))

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, allow_intra_route: bool = True):
    return CustomerSwapNeighborhood(problem, allow_intra_route=allow_intra_route)
