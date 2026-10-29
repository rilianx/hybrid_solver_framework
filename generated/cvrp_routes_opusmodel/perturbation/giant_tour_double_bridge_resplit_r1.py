from random import Random
from generated.cvrp_routes_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "giant_tour_double_bridge_resplit",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "max_moves": {"type": "int", "range": [1, 10]},
        "split": {"type": "cat", "values": ["optimal", "greedy"]},
        "shuffle_routes": {"type": "bool"},
    },
}


def _force_change(routes, rng):
    routes = [list(r) for r in routes if r]
    total = sum(len(r) for r in routes)
    if total < 2:
        return routes
    long_idx = [i for i, r in enumerate(routes) if len(r) >= 2]
    if long_idx:
        i = rng.choice(long_idx)
        r = routes[i]
        cut = rng.randint(1, len(r) - 1)
        routes[i] = r[:cut]
        routes.append(r[cut:])
    else:
        i, j = rng.sample(range(len(routes)), 2)
        routes[i] = routes[i] + routes[j]
        routes.pop(j)
    return routes


class GiantTourDoubleBridgeResplit:
    def __init__(self, problem, max_moves=3, split="optimal", shuffle_routes=True):
        self.inst = problem.inst
        self.max_moves = int(max_moves)
        self.split = split
        self.shuffle_routes = bool(shuffle_routes)

    def _double_bridge(self, t, rng):
        n = len(t)
        if n >= 4:
            a, b, c = sorted(rng.sample(range(1, n), 3))
            return t[:a] + t[b:c] + t[a:b] + t[c:]
        if n >= 2:
            i, j = rng.sample(range(n), 2)
            t = list(t)
            t[i], t[j] = t[j], t[i]
        return t

    def _greedy_split(self, t):
        inst = self.inst
        cap = inst.capacity + 1e-9
        routes, cur, load = [], [], 0.0
        for c in t:
            d = inst.demand[c]
            if cur and load + d > cap:
                routes.append(cur)
                cur, load = [], 0.0
            cur.append(c)
            load += d
        if cur:
            routes.append(cur)
        return routes

    def _optimal_split(self, t):
        inst = self.inst
        cap = inst.capacity + 1e-9
        n = len(t)
        INF = float("inf")
        V = [INF] * (n + 1)
        P = [0] * (n + 1)
        V[0] = 0.0
        for i in range(n):
            if V[i] == INF:
                continue
            load = 0.0
            cost = 0.0
            for j in range(i, n):
                load += inst.demand[t[j]]
                if load > cap and j > i:
                    break
                if j == i:
                    cost = inst.dist(0, t[j]) + inst.dist(t[j], 0)
                else:
                    cost += (inst.dist(t[j - 1], t[j]) + inst.dist(t[j], 0)
                             - inst.dist(t[j - 1], 0))
                if V[i] + cost < V[j + 1]:
                    V[j + 1] = V[i] + cost
                    P[j + 1] = i
        routes = []
        j = n
        while j > 0:
            i = P[j]
            routes.append(list(t[i:j]))
            j = i
        routes.reverse()
        return routes

    def perturb(self, sol, strength: float, rng: Random):
        base = canonical(sol)
        routes = [list(r) for r in base]
        if self.shuffle_routes:
            rng.shuffle(routes)
        t = [c for r in routes for c in r]
        if not t:
            return base
        moves = max(1, min(self.max_moves, int(round(strength))))
        for _ in range(moves):
            t = self._double_bridge(t, rng)
        if self.split == "optimal":
            new_routes = self._optimal_split(t)
        else:
            new_routes = self._greedy_split(t)
        new = canonical(new_routes)
        if new == base:
            new = canonical(_force_change(base, rng))
        return new


def build_component(problem, max_moves=3, split="optimal", shuffle_routes=True):
    return GiantTourDoubleBridgeResplit(problem, max_moves=max_moves, split=split,
                                        shuffle_routes=shuffle_routes)
