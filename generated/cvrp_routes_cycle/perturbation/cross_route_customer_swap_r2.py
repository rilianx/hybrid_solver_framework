from __future__ import annotations

from random import Random
from typing import List, Tuple

from generated.cvrp_routes_cycle.model.parts import canonical


COMPONENT = {
    "name": "cross_route_customer_swap",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 20.0]}
    },
}


class CrossRouteCustomerSwap:
    def __init__(self, problem):
        self.problem = problem

    def perturb(self, sol, strength: float, rng: Random):
        sol = canonical(sol)
        if not sol:
            return sol

        routes = [list(route) for route in sol]
        non_empty = [i for i, r in enumerate(routes) if len(r) >= 2]
        if not non_empty:
            return sol

        # Kick by reversing or cyclically rotating whole routes.
        # This operates at route scale, distinct from contiguous-segment relocation.
        moves = max(1, int(round(strength)))

        for _ in range(moves):
            i = rng.choice(non_empty)
            route = routes[i]
            n = len(route)
            if n < 2:
                continue

            if n == 2:
                route[0], route[1] = route[1], route[0]
            else:
                if rng.random() < 0.5:
                    # Full route reversal
                    route.reverse()
                else:
                    # Cyclic shift of the entire route
                    shift = rng.randrange(1, n)
                    routes[i] = route[shift:] + route[:shift]

        out = canonical(tuple(tuple(r) for r in routes))
        return out if out != sol else canonical(tuple(tuple(r) for r in routes))

        

def build_component(problem, **params):
    return CrossRouteCustomerSwap(problem)
