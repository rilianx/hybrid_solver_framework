from random import Random
from generated.cvrp_routes_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "spatial_ruin_noisy_cheapest_reinsert",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "scale": {"type": "float", "range": [0.5, 3.0]},
        "noise": {"type": "float", "range": [0.0, 0.5]},
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


class SpatialRuinNoisyCheapestReinsert:
    def __init__(self, problem, scale=2.0, noise=0.1):
        self.inst = problem.inst
        self.scale = float(scale)
        self.noise = float(noise)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        base = canonical(sol)
        routes = [list(r) for r in base]
        custs = [c for r in routes for c in r]
        if not custs:
            return base
        k = max(1, min(len(custs), int(round(strength * self.scale))))
        seed = rng.choice(custs)
        others = sorted((c for c in custs if c != seed), key=lambda c: (inst.dist(seed, c), c))
        removed = [seed] + others[:k - 1]
        rs = set(removed)
        routes = [[c for c in r if c not in rs] for r in routes]
        routes = [r for r in routes if r]
        loads = [sum(inst.demand[c] for c in r) for r in routes]
        cap = inst.capacity + 1e-9
        rng.shuffle(removed)
        for c in removed:
            d = inst.demand[c]
            best_cost = (2.0 * inst.dist(0, c)) * (1.0 + self.noise * rng.random())
            best = None
            for i, r in enumerate(routes):
                if loads[i] + d > cap:
                    continue
                prev = 0
                for pos in range(len(r) + 1):
                    nxt = r[pos] if pos < len(r) else 0
                    delta = inst.dist(prev, c) + inst.dist(c, nxt) - inst.dist(prev, nxt)
                    delta *= 1.0 + self.noise * rng.random()
                    if delta < best_cost:
                        best_cost = delta
                        best = (i, pos)
                    prev = nxt
            if best is None:
                routes.append([c])
                loads.append(d)
            else:
                i, pos = best
                routes[i].insert(pos, c)
                loads[i] += d
        new = canonical(routes)
        if new == base:
            new = canonical(_force_change(base, rng))
        return new


def build_component(problem, scale=2.0, noise=0.1):
    return SpatialRuinNoisyCheapestReinsert(problem, scale=scale, noise=noise)
