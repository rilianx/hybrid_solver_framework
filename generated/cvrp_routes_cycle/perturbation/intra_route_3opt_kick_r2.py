from random import Random
from typing import List

COMPONENT = {
    "name": "intra_route_3opt_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class IntraRoute3OptKickPerturbation:
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
        nontrivial = [idx for idx, r in enumerate(routes) if len(r) >= 3]
        if not nontrivial:
            two_plus = [idx for idx, r in enumerate(routes) if len(r) >= 2]
            if two_plus:
                idx = rng.choice(two_plus)
                r = routes[idx][:]
                i, j = sorted(rng.sample(range(len(r)), 2))
                r[i : j + 1] = reversed(r[i : j + 1])
                routes[idx] = r
                return self._from_routes(routes)
            if len(routes) >= 2:
                a, b = rng.sample(range(len(routes)), 2)
                routes[a], routes[b] = routes[b], routes[a]
                return self._from_routes(routes)
            return self._from_routes(routes)

        idx = rng.choice(nontrivial)
        r = routes[idx][:]
        n = len(r)

        # 3-opt style kick, implemented as a single elementary reconnection
        # on a route segment. For a route of length n, choose three segments
        # by sampling two cut points; the third segment is the suffix.
        i, j = sorted(rng.sample(range(1, n), 2))

        mode = int(strength) % 3
        a = r[:i]
        b = r[i:j]
        c = r[j:]
        if mode == 0:
            r = a + list(reversed(b)) + c
        elif mode == 1:
            r = a + c + b
        else:
            r = c + b + a

        routes[idx] = r
        return self._from_routes(routes)


def build_component(problem, **params):
    _ = params.get("strength", 2.0)
    return IntraRoute3OptKickPerturbation(problem)
