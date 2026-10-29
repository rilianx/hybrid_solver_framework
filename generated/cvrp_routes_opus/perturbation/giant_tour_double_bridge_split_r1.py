from random import Random

from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "giant_tour_double_bridge_split",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "split_mode": {"type": "cat", "values": ["optimal", "greedy"]},
        "reverse_prob": {"type": "float", "range": [0.0, 1.0]},
        "max_attempts": {"type": "int", "range": [1, 20]},
    },
}


def _load(inst, route):
    return sum(inst.demand[c] for c in route)


def _force_change(inst, base, rng):
    routes = [list(r) for r in base]
    multi = [i for i, r in enumerate(routes) if len(r) >= 2]
    if multi:
        i = rng.choice(multi)
        c = routes[i].pop(rng.randrange(len(routes[i])))
        routes.append([c])
        return canonical(routes)
    if len(routes) >= 2:
        pairs = [
            (i, j)
            for i in range(len(routes))
            for j in range(len(routes))
            if i != j and _load(inst, routes[i]) + _load(inst, routes[j]) <= inst.capacity
        ]
        i, j = rng.choice(pairs) if pairs else rng.sample(range(len(routes)), 2)
        routes[i].extend(routes[j])
        routes[j] = []
    return canonical(routes)


class GiantTourDoubleBridgeSplit:
    def __init__(self, problem, split_mode="optimal", reverse_prob=0.3, max_attempts=5):
        self.inst = problem.inst
        self.split_mode = split_mode
        self.reverse_prob = float(reverse_prob)
        self.max_attempts = int(max_attempts)

    def _kick(self, tour, rng):
        n = len(tour)
        if n >= 8:
            a, b, c = sorted(rng.sample(range(1, n), 3))
            return tour[:a] + tour[b:c] + tour[a:b] + tour[c:]
        if n >= 2:
            i, j = sorted(rng.sample(range(n), 2))
            if rng.random() < 0.5:
                return tour[:i] + tour[i:j + 1][::-1] + tour[j + 1:]
            t = list(tour)
            t[i], t[j] = t[j], t[i]
            return t
        return tour

    def _split_optimal(self, tour):
        inst = self.inst
        n = len(tour)
        inf = float("inf")
        V = [inf] * (n + 1)
        P = [0] * (n + 1)
        V[0] = 0.0
        for i in range(n):
            if V[i] == inf:
                continue
            load = 0.0
            cost = 0.0
            for j in range(i, n):
                cj = tour[j]
                load += inst.demand[cj]
                if j > i and load > inst.capacity:
                    break
                if j == i:
                    cost = inst.dist(0, cj) + inst.dist(cj, 0)
                else:
                    cp = tour[j - 1]
                    cost += inst.dist(cp, cj) - inst.dist(cp, 0) + inst.dist(cj, 0)
                if V[i] + cost < V[j + 1]:
                    V[j + 1] = V[i] + cost
                    P[j + 1] = i
        routes = []
        j = n
        while j > 0:
            i = P[j]
            routes.append(tuple(tour[i:j]))
            j = i
        return routes

    def _split_greedy(self, tour):
        inst = self.inst
        routes, cur, load = [], [], 0.0
        for c in tour:
            d = inst.demand[c]
            if cur and load + d > inst.capacity:
                routes.append(tuple(cur))
                cur, load = [], 0.0
            cur.append(c)
            load += d
        if cur:
            routes.append(tuple(cur))
        return routes

    def perturb(self, sol, strength: float, rng: Random):
        base = canonical(sol)
        if sum(len(r) for r in base) <= 1:
            return base
        k = max(1, int(round(strength)))
        for _ in range(self.max_attempts):
            rs = [list(r) for r in base]
            rng.shuffle(rs)
            tour = []
            for r in rs:
                if rng.random() < self.reverse_prob:
                    r = r[::-1]
                tour.extend(r)
            for _k in range(k):
                tour = self._kick(tour, rng)
            if self.split_mode == "optimal":
                routes = self._split_optimal(tour)
            else:
                routes = self._split_greedy(tour)
            new = canonical(routes)
            if new != base:
                return new
        return _force_change(self.inst, base, rng)


def build_component(problem, split_mode="optimal", reverse_prob=0.3, max_attempts=5):
    return GiantTourDoubleBridgeSplit(problem, split_mode, reverse_prob, max_attempts)
