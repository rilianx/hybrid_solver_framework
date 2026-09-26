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
        candidates = [idx for idx, r in enumerate(routes) if len(r) >= 4]
        if not candidates:
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

        idx = rng.choice(candidates)
        r = routes[idx][:]
        n = len(r)

        # Double-bridge style intra-route kick:
        # choose 4 cut points and reconnect the four segments as
        # A + C + B + D, which changes multiple adjacencies at once and
        # reaches neighborhoods different from simple segment exchange.
        #
        # For short routes, use a robust fallback to a larger reversal.
        if n < 8:
            i, j = sorted(rng.sample(range(1, n), 2))
            r[i:j] = reversed(r[i:j])
            routes[idx] = r
            return self._from_routes(routes)

        cuts = sorted(rng.sample(range(1, n), 4))
        a, b, c, d = cuts
        A = r[:a]
        B = r[a:b]
        C = r[b:c]
        D = r[c:d]
        E = r[d:]

        mode = int(strength) % 3
        if mode == 0:
            r = A + C + B + D + E
        elif mode == 1:
            r = A + D + C + B + E
        else:
            r = A + C + D + B + E

        routes[idx] = r
        return self._from_routes(routes)


def build_component(problem, **params):
    _ = params.get("strength", 2.0)
    return IntraRoute3OptKickPerturbation(problem)
