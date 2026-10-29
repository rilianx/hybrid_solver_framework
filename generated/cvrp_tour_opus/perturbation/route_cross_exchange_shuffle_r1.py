from random import Random

from generated.cvrp_tour_cycle.model.parts import canonical

COMPONENT = {
    "name": "route_cross_exchange_shuffle",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "max_seg_len": {"type": "int", "range": [1, 6]},
        "shuffle_routes": {"type": "bool"},
    },
}


class RouteCrossExchangeShuffle:
    def __init__(self, problem, max_seg_len=3, shuffle_routes=True):
        self.problem = problem
        self.inst = problem.inst
        self.max_seg_len = max(1, int(max_seg_len))
        self.shuffle_routes = bool(shuffle_routes)

    def _greedy_routes(self, tour):
        routes, cur, load = [], [], 0.0
        cap = self.inst.capacity
        dem = self.inst.demand
        for c in tour:
            d = dem[c]
            if cur and load + d > cap:
                routes.append(cur)
                cur, load = [], 0.0
            cur.append(c)
            load += d
        if cur:
            routes.append(cur)
        return routes

    def perturb(self, sol, strength: float, rng: Random):
        orig = list(sol)
        n = len(orig)
        if n < 2:
            return canonical(tuple(orig))
        routes = self._greedy_routes(orig)
        k = max(1, int(round(strength)))
        for _ in range(k):
            if len(routes) >= 2:
                i, j = rng.sample(range(len(routes)), 2)
                r1, r2 = routes[i], routes[j]
                l1 = rng.randint(1, min(self.max_seg_len, len(r1)))
                l2 = rng.randint(1, min(self.max_seg_len, len(r2)))
                p1 = rng.randint(0, len(r1) - l1)
                p2 = rng.randint(0, len(r2) - l2)
                s1, s2 = r1[p1:p1 + l1], r2[p2:p2 + l2]
                if rng.random() < 0.5:
                    s1 = s1[::-1]
                if rng.random() < 0.5:
                    s2 = s2[::-1]
                routes[i] = r1[:p1] + s2 + r1[p1 + l1:]
                routes[j] = r2[:p2] + s1 + r2[p2 + l2:]
                routes = [r for r in routes if r]
            else:
                r = routes[0]
                if len(r) >= 2:
                    a, b = sorted(rng.sample(range(len(r) + 1), 2))
                    if b - a < 2:
                        a, b = 0, len(r)
                    routes[0] = r[:a] + r[a:b][::-1] + r[b:]
        if self.shuffle_routes and len(routes) >= 2:
            rng.shuffle(routes)
        t = [c for r in routes for c in r]
        if t == orig:
            i, j = rng.sample(range(n), 2)
            t = list(orig)
            t[i], t[j] = t[j], t[i]
        return canonical(tuple(t))


def build_component(problem, max_seg_len=3, shuffle_routes=True):
    return RouteCrossExchangeShuffle(problem, max_seg_len, shuffle_routes)
