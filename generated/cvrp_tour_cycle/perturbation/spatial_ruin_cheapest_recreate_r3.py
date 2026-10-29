from random import Random

from generated.cvrp_tour_cycle.model.parts import canonical
import math

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
        if n < 4:
            t = list(orig)
            i, j = rng.sample(range(n), 2)
            t[i], t[j] = t[j], t[i]
            return canonical(tuple(t))
        kicks = max(1, int(math.ceil(max(0.0, float(strength)) * self.rps / 5.0)))
        kicks = min(kicks, max(1, n // 4))
        t = list(orig)
        for _ in range(kicks):
            p1, p2, p3 = sorted(rng.sample(range(1, n), 3))
            a = t[:p1]
            b = t[p1:p2]
            c = t[p2:p3]
            d = t[p3:]
            if self.noise > 0.0 and rng.random() < self.noise:
                b = b[::-1]
            if self.noise > 0.0 and rng.random() < self.noise:
                c = c[::-1]
            t = a + c + b + d
        if t == orig:
            i, j = rng.sample(range(n), 2)
            t = list(orig)
            t[i], t[j] = t[j], t[i]
        return canonical(tuple(t))


def build_component(problem, ruin_per_strength=2, noise=0.1):
    return SpatialRuinCheapestRecreate(problem, ruin_per_strength, noise)
