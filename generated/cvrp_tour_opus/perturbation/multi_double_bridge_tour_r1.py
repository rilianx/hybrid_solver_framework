from random import Random

from generated.cvrp_tour_cycle.model.parts import canonical

COMPONENT = {
    "name": "multi_double_bridge_tour",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"bridges_per_strength": {"type": "int", "range": [1, 3]}},
}


def _fallback_swap(t, rng):
    n = len(t)
    if n < 2:
        return t
    i, j = rng.sample(range(n), 2)
    t = list(t)
    t[i], t[j] = t[j], t[i]
    return t


class MultiDoubleBridgeTour:
    def __init__(self, problem, bridges_per_strength=1):
        self.problem = problem
        self.bps = max(1, int(bridges_per_strength))

    def perturb(self, sol, strength: float, rng: Random):
        orig = list(sol)
        n = len(orig)
        if n < 2:
            return canonical(tuple(orig))
        t = list(orig)
        k = max(1, int(round(strength))) * self.bps
        if n >= 4:
            for _ in range(k):
                a, b, c = sorted(rng.sample(range(1, n), 3))
                t = t[:a] + t[b:c] + t[a:b] + t[c:]
        else:
            for _ in range(k):
                t = _fallback_swap(t, rng)
        if t == orig:
            t = _fallback_swap(orig, rng)
        return canonical(tuple(t))


def build_component(problem, bridges_per_strength=1):
    return MultiDoubleBridgeTour(problem, bridges_per_strength)
