from random import Random

from generated.cvrp_tour_cycle.model.parts import canonical

COMPONENT = {
    "name": "spatial_ruin_cheapest_recreate",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "ruin_per_strength": {"type": "int", "range": [1, 5]},
        "noise": {"type": "float", "range": [0.0, 0.5]},
    },
}


class SpatialRuinCheapestRecreate:
    def __init__(self, problem, ruin_per_strength=2, noise=0.1):
        self.problem = problem
        self.inst = problem.inst
        self.rps = max(1, int(ruin_per_strength))
        self.noise = float(noise)

    def perturb(self, sol, strength: float, rng: Random):
        orig = list(sol)
        n = len(orig)
        if n < 2:
            return canonical(tuple(orig))
        dist = self.inst.dist
        k = max(1, int(round(strength))) * self.rps
        k = max(1, min(n - 1, k))
        seed = rng.choice(orig)
        ranked = sorted(orig, key=lambda c: dist(seed, c))
        removed = ranked[:k]
        rem_set = set(removed)
        t = [c for c in orig if c not in rem_set]
        rng.shuffle(removed)
        for c in removed:
            best_pos, best_cost = 0, None
            m = len(t)
            for pos in range(m + 1):
                p = t[pos - 1] if pos > 0 else 0
                q = t[pos] if pos < m else 0
                delta = dist(p, c) + dist(c, q) - dist(p, q)
                if self.noise > 0.0:
                    delta *= 1.0 + self.noise * rng.random()
                if best_cost is None or delta < best_cost:
                    best_cost, best_pos = delta, pos
            t.insert(best_pos, c)
        if t == orig:
            i, j = rng.sample(range(n), 2)
            t = list(orig)
            t[i], t[j] = t[j], t[i]
        return canonical(tuple(t))


def build_component(problem, ruin_per_strength=2, noise=0.1):
    return SpatialRuinCheapestRecreate(problem, ruin_per_strength, noise)
