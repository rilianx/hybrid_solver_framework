from random import Random
from generated.cvrp_routes_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "random_relocate_k_capacity_aware",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "scale": {"type": "float", "range": [0.5, 3.0]},
        "new_route_prob": {"type": "float", "range": [0.0, 0.3]},
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


class RandomRelocateKCapacityAware:
    def __init__(self, problem, scale=1.0, new_route_prob=0.05):
        self.inst = problem.inst
        self.scale = float(scale)
        self.new_route_prob = float(new_route_prob)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        base = canonical(sol)
        routes = [list(r) for r in base]
        custs = [c for r in routes for c in r]
        if not custs:
            return base
        k = max(1, min(len(custs), int(round(strength * self.scale))))
        chosen = rng.sample(custs, k)
        cs = set(chosen)
        routes = [[c for c in r if c not in cs] for r in routes]
        routes = [r for r in routes if r]
        loads = [sum(inst.demand[c] for c in r) for r in routes]
        cap = inst.capacity + 1e-9
        for c in chosen:
            d = inst.demand[c]
            feas = [i for i in range(len(routes)) if loads[i] + d <= cap]
            if feas and rng.random() >= self.new_route_prob:
                i = rng.choice(feas)
                pos = rng.randint(0, len(routes[i]))
                routes[i].insert(pos, c)
                loads[i] += d
            else:
                routes.append([c])
                loads.append(d)
        new = canonical(routes)
        if new == base:
            new = canonical(_force_change(base, rng))
        return new


def build_component(problem, scale=1.0, new_route_prob=0.05):
    return RandomRelocateKCapacityAware(problem, scale=scale, new_route_prob=new_route_prob)
