from random import Random

from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "random_interroute_relocate_swap",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "relocate_prob": {"type": "float", "range": [0.0, 1.0]},
        "max_tries": {"type": "int", "range": [1, 50]},
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
        if pairs:
            i, j = rng.choice(pairs)
        else:
            i, j = rng.sample(range(len(routes)), 2)
        routes[i].extend(routes[j])
        routes[j] = []
    return canonical(routes)


class RandomInterRouteRelocateSwap:
    def __init__(self, problem, relocate_prob=0.6, max_tries=10):
        self.inst = problem.inst
        self.relocate_prob = float(relocate_prob)
        self.max_tries = int(max_tries)

    def _relocate(self, routes, rng):
        inst = self.inst
        src = rng.randrange(len(routes))
        if not routes[src]:
            return False
        pos = rng.randrange(len(routes[src]))
        c = routes[src][pos]
        tgt = rng.randrange(len(routes) + 1)
        if tgt == src:
            return False
        if tgt == len(routes):
            if len(routes[src]) < 2:
                return False
            routes[src].pop(pos)
            routes.append([c])
            return True
        if _load(inst, routes[tgt]) + inst.demand[c] > inst.capacity:
            return False
        routes[src].pop(pos)
        routes[tgt].insert(rng.randrange(len(routes[tgt]) + 1), c)
        return True

    def _swap(self, routes, rng):
        inst = self.inst
        if len(routes) < 2:
            return False
        a, b = rng.sample(range(len(routes)), 2)
        if not routes[a] or not routes[b]:
            return False
        i = rng.randrange(len(routes[a]))
        j = rng.randrange(len(routes[b]))
        ca, cb = routes[a][i], routes[b][j]
        la = _load(inst, routes[a]) - inst.demand[ca] + inst.demand[cb]
        lb = _load(inst, routes[b]) - inst.demand[cb] + inst.demand[ca]
        if la > inst.capacity or lb > inst.capacity:
            return False
        routes[a][i], routes[b][j] = cb, ca
        return True

    def perturb(self, sol, strength: float, rng: Random):
        base = canonical(sol)
        if sum(len(r) for r in base) <= 1:
            return base
        routes = [list(r) for r in base]
        k = max(1, int(round(strength)))
        for _ in range(k):
            for _t in range(self.max_tries):
                if rng.random() < self.relocate_prob:
                    ok = self._relocate(routes, rng)
                else:
                    ok = self._swap(routes, rng)
                routes = [r for r in routes if r]
                if ok:
                    break
        new = canonical(routes)
        if new == base:
            new = _force_change(self.inst, base, rng)
        return new


def build_component(problem, relocate_prob=0.6, max_tries=10):
    return RandomInterRouteRelocateSwap(problem, relocate_prob, max_tries)
