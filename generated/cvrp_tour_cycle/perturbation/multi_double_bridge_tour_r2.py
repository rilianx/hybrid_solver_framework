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
        k = max(1, int(round(strength))) * self.bps
        if n >= 4:
            c = min(n - 1, 3 * k)
            cuts = sorted(rng.sample(range(1, n), c))
            bounds = [0] + cuts + [n]
            segs = [orig[bounds[i]:bounds[i + 1]] for i in range(len(bounds) - 1)]
            order = _reorder_segments(len(segs), rng)
            t = []
            for idx in order:
                t.extend(segs[idx])
        else:
            t = list(orig)
            for _ in range(k):
                t = _fallback_swap(t, rng)
        if t == orig:
            t = _fallback_swap(orig, rng)
        return canonical(tuple(t))


def build_component(problem, bridges_per_strength=1):
    return MultiDoubleBridgeTour(problem, bridges_per_strength)


def _reorder_segments(m, rng, tries=50):
    rest = list(range(1, m))
    for _ in range(tries):
        rng.shuffle(rest)
        order = [0] + rest
        if all(order[i + 1] != order[i] + 1 for i in range(len(order) - 1)):
            return order
    if m >= 3:
        return [0] + list(range(m - 1, 0, -1))
    return [0] + rest
