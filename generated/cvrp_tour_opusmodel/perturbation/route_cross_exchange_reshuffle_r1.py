from random import Random

from generated.cvrp_tour_opusmodel.model.parts import canonical, _decode

COMPONENT = {
    "name": "route_cross_exchange_reshuffle",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "max_seg": {"type": "int", "range": [1, 6]},
        "route_shuffle_prob": {"type": "float", "range": [0.0, 1.0]},
        "route_reverse_prob": {"type": "float", "range": [0.0, 0.5]},
    },
}


class RouteCrossExchangeReshuffle:
    def __init__(self, problem, max_seg=3, route_shuffle_prob=0.5, route_reverse_prob=0.2):
        self.problem = problem
        self.inst = problem.inst
        self.max_seg = int(max_seg)
        self.route_shuffle_prob = float(route_shuffle_prob)
        self.route_reverse_prob = float(route_reverse_prob)

    def _segment(self, r, rng):
        L = len(r)
        length = rng.randint(0, min(self.max_seg, L))
        i = rng.randint(0, L - length)
        return i, i + length

    def perturb(self, sol, strength: float, rng: Random):
        base = list(canonical(sol))
        n = len(base)
        if n < 2:
            return canonical(base)
        routes, _ = _decode(self.inst, tuple(base))
        routes = [list(r) for r in routes if r]
        seen = set(c for r in routes for c in r)
        missing = [c for c in base if c not in seen]
        if missing:
            routes.append(missing)
        k = max(1, int(round(strength)))
        if len(routes) >= 2:
            for _ in range(k):
                a, b = rng.sample(range(len(routes)), 2)
                ra, rb = routes[a], routes[b]
                for _try in range(4):
                    i1, j1 = self._segment(ra, rng)
                    i2, j2 = self._segment(rb, rng)
                    if j1 > i1 or j2 > i2:
                        break
                segA, segB = ra[i1:j1], rb[i2:j2]
                if rng.random() < 0.5:
                    segA = segA[::-1]
                if rng.random() < 0.5:
                    segB = segB[::-1]
                routes[a] = ra[:i1] + segB + ra[j1:]
                routes[b] = rb[:i2] + segA + rb[j2:]
                routes = [r for r in routes if r]
                if len(routes) < 2:
                    break
        else:
            r = routes[0]
            for _ in range(k):
                if len(r) >= 2:
                    i, j = sorted(rng.sample(range(len(r)), 2))
                    r = r[:i] + r[i:j + 1][::-1] + r[j + 1:]
            routes = [r]
        routes = [r[::-1] if rng.random() < self.route_reverse_prob else r for r in routes]
        if rng.random() < self.route_shuffle_prob:
            rng.shuffle(routes)
        tour = [c for r in routes for c in r]
        if tour == base:
            i, j = rng.sample(range(n), 2)
            tour = list(base)
            tour[i], tour[j] = tour[j], tour[i]
        return canonical(tour)


def build_component(problem, max_seg=3, route_shuffle_prob=0.5, route_reverse_prob=0.2):
    return RouteCrossExchangeReshuffle(
        problem,
        max_seg=max_seg,
        route_shuffle_prob=route_shuffle_prob,
        route_reverse_prob=route_reverse_prob,
    )
