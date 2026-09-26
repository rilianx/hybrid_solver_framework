from random import Random
from typing import List

COMPONENT = {
    "name": "route_segment_exchange",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class RouteSegmentExchangePerturbation:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical
        self.inst = problem.inst

    def _as_routes(self, sol) -> List[List[int]]:
        return [list(route) for route in self.canonical(sol)]

    def _from_routes(self, routes: List[List[int]]):
        return self.canonical(tuple(tuple(route) for route in routes))

    def perturb(self, sol, strength: float, rng: Random):
        routes = self._as_routes(sol)
        if len(routes) == 0:
            return self._from_routes([[]])
        if len(routes) == 1:
            r = routes[0]
            if len(r) < 2:
                return self._from_routes(routes)
            i, j = sorted(rng.sample(range(len(r)), 2))
            r2 = r[:i] + list(reversed(r[i : j + 1])) + r[j + 1 :]
            return self._from_routes([r2])

        i1, i2 = rng.sample(range(len(routes)), 2)
        r1, r2 = routes[i1], routes[i2]
        if not r1 or not r2:
            return self._from_routes(routes)

        # Exchange suffixes or middle segments depending on strength.
        len1 = len(r1)
        len2 = len(r2)
        cut1a = rng.randint(0, len1 - 1)
        cut1b = rng.randint(cut1a + 1, len1)
        cut2a = rng.randint(0, len2 - 1)
        cut2b = rng.randint(cut2a + 1, len2)

        seg1 = r1[cut1a:cut1b]
        seg2 = r2[cut2a:cut2b]

        new_r1 = r1[:cut1a] + seg2 + r1[cut1b:]
        new_r2 = r2[:cut2a] + seg1 + r2[cut2b:]

        new_routes = []
        for idx, route in enumerate(routes):
            if idx == i1:
                if new_r1:
                    new_routes.append(new_r1)
            elif idx == i2:
                if new_r2:
                    new_routes.append(new_r2)
            else:
                new_routes.append(route)

        return self._from_routes(new_routes)


def build_component(problem, **params):
    _ = params.get("strength", 2.0)
    return RouteSegmentExchangePerturbation(problem)
