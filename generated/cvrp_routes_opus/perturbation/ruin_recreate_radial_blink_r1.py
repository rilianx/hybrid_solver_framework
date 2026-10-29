from random import Random

from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "ruin_recreate_radial_blink",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "removal_factor": {"type": "int", "range": [1, 5]},
        "ruin_mode": {"type": "cat", "values": ["radial", "random"]},
        "insert_order": {"type": "cat", "values": ["random", "demand_desc", "far_first"]},
        "blink_rate": {"type": "float", "range": [0.0, 0.3]},
        "max_attempts": {"type": "int", "range": [1, 10]},
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


class RuinRecreateRadialBlink:
    def __init__(self, problem, removal_factor=2, ruin_mode="radial",
                 insert_order="random", blink_rate=0.05, max_attempts=3):
        self.inst = problem.inst
        self.removal_factor = int(removal_factor)
        self.ruin_mode = ruin_mode
        self.insert_order = insert_order
        self.blink_rate = float(blink_rate)
        self.max_attempts = int(max_attempts)

    def _ruin(self, base, k, rng):
        inst = self.inst
        customers = [c for r in base for c in r]
        if self.ruin_mode == "radial":
            seed = rng.choice(customers)
            customers.sort(key=lambda c: (inst.dist(seed, c), c))
            removed = customers[:k]
        else:
            removed = rng.sample(customers, k)
        rem = set(removed)
        routes = [[c for c in r if c not in rem] for r in base]
        routes = [r for r in routes if r]
        return routes, removed

    def _recreate(self, routes, removed, rng):
        inst = self.inst
        if self.insert_order == "demand_desc":
            removed = sorted(removed, key=lambda c: (-inst.demand[c], rng.random()))
        elif self.insert_order == "far_first":
            removed = sorted(removed, key=lambda c: (-inst.dist(0, c), rng.random()))
        else:
            removed = list(removed)
            rng.shuffle(removed)
        loads = [_load(inst, r) for r in routes]
        for c in removed:
            d = inst.demand[c]
            best_cost = 2.0 * inst.dist(0, c)
            best = None
            for ri, r in enumerate(routes):
                if loads[ri] + d > inst.capacity:
                    continue
                for p in range(len(r) + 1):
                    if rng.random() < self.blink_rate:
                        continue
                    a = r[p - 1] if p > 0 else 0
                    b = r[p] if p < len(r) else 0
                    delta = inst.dist(a, c) + inst.dist(c, b) - inst.dist(a, b)
                    if delta < best_cost:
                        best_cost = delta
                        best = (ri, p)
            if best is None:
                routes.append([c])
                loads.append(d)
            else:
                ri, p = best
                routes[ri].insert(p, c)
                loads[ri] += d
        return routes

    def perturb(self, sol, strength: float, rng: Random):
        base = canonical(sol)
        n = sum(len(r) for r in base)
        if n <= 1:
            return base
        k = max(1, min(n, int(round(max(1.0, strength) * self.removal_factor))))
        for _ in range(self.max_attempts):
            routes, removed = self._ruin(base, k, rng)
            routes = self._recreate(routes, removed, rng)
            new = canonical(routes)
            if new != base:
                return new
        return _force_change(self.inst, base, rng)


def build_component(problem, removal_factor=2, ruin_mode="radial",
                    insert_order="random", blink_rate=0.05, max_attempts=3):
    return RuinRecreateRadialBlink(problem, removal_factor, ruin_mode,
                                   insert_order, blink_rate, max_attempts)
