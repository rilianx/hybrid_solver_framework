from __future__ import annotations

from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "cross_route_swap_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class CrossRouteSwapPerturbation:
    def __init__(self, problem: Any):
        self.problem = problem

    def perturb(self, sol, strength: float, rng: Random):
        routes = [list(r) for r in sol]
        if not routes:
            return sol

        nonempty = [idx for idx, r in enumerate(routes) if r]
        if not nonempty:
            return sol

        # Prefer an inter-route swap when possible; otherwise do an intra-route swap.
        if len(nonempty) >= 2:
            r1, r2 = rng.sample(nonempty, 2)
            route1 = routes[r1]
            route2 = routes[r2]

            # Swap one customer from each route. This is an elementary move and
            # cannot be a no-op because the routes are distinct.
            i1 = rng.randrange(len(route1))
            i2 = rng.randrange(len(route2))
            c1 = route1[i1]
            c2 = route2[i2]
            route1[i1], route2[i2] = c2, c1
            return canonical(tuple(tuple(r) for r in routes))

        # Single route case: swap two distinct customers if possible.
        r = nonempty[0]
        route = routes[r]
        if len(route) < 2:
            return sol

        i, j = rng.sample(range(len(route)), 2)
        route[i], route[j] = route[j], route[i]
        return canonical(tuple(tuple(r_) for r_ in routes))


def build_component(problem, **params):
    _strength = params.get("strength", 3.0)
    return CrossRouteSwapPerturbation(problem)
