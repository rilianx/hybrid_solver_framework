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
        non_empty = [i for i, r in enumerate(routes) if r]
        if len(non_empty) == 0:
            return sol

        # Number of swap attempts grows with strength, but at least one.
        attempts = max(1, int(round(strength)))

        for _ in range(attempts):
            if len(non_empty) == 1:
                i = non_empty[0]
                if len(routes[i]) >= 2:
                    a, b = rng.sample(range(len(routes[i])), 2)
                    routes[i][a], routes[i][b] = routes[i][b], routes[i][a]
                    out = canonical(tuple(tuple(r) for r in routes))
                    if out != sol:
                        return out
                continue

            i, j = rng.sample(non_empty, 2)
            ri, rj = routes[i], routes[j]
            if not ri or not rj:
                continue

            ai = rng.randrange(len(ri))
            aj = rng.randrange(len(rj))
            ri[ai], rj[aj] = rj[aj], ri[ai]

            out = canonical(tuple(tuple(r) for r in routes))
            if out != sol:
                return out

            # revert if no change after canonicalization due to symmetry
            ri[ai], rj[aj] = rj[aj], ri[ai]

        # fallback: within-route swap on a route with at least 2 customers
        candidates = [i for i, r in enumerate(routes) if len(r) >= 2]
        if candidates:
            i = rng.choice(candidates)
            a, b = rng.sample(range(len(routes[i])), 2)
            routes[i][a], routes[i][b] = routes[i][b], routes[i][a]

        out = canonical(tuple(tuple(r) for r in routes))
        return out if out != sol else canonical(tuple(tuple(r) for r in routes))

        

def build_component(problem, **params):
    return CrossRouteCustomerSwap(problem)
