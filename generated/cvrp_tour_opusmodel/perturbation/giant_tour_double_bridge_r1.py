from random import Random

from generated.cvrp_tour_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "giant_tour_double_bridge",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"reverse_prob": {"type": "float", "range": [0.0, 0.5]}},
}


class GiantTourDoubleBridge:
    def __init__(self, problem, reverse_prob=0.2):
        self.problem = problem
        self.reverse_prob = float(reverse_prob)

    @staticmethod
    def _swap_fallback(s, rng):
        if len(s) < 2:
            return s
        i, j = rng.sample(range(len(s)), 2)
        s = list(s)
        s[i], s[j] = s[j], s[i]
        return s

    def perturb(self, sol, strength: float, rng: Random):
        base = list(canonical(sol))
        n = len(base)
        if n < 2:
            return canonical(base)
        k = max(1, int(round(strength)))
        s = list(base)
        for _ in range(k):
            if n < 4:
                s = self._swap_fallback(s, rng)
                continue
            a, b, c = sorted(rng.sample(range(1, n), 3))
            A, B, C, D = s[:a], s[a:b], s[b:c], s[c:]
            if rng.random() < self.reverse_prob:
                B = B[::-1]
            if rng.random() < self.reverse_prob:
                C = C[::-1]
            s = A + C + B + D
        if s == base:
            s = self._swap_fallback(base, rng)
        return canonical(s)


def build_component(problem, reverse_prob=0.2):
    return GiantTourDoubleBridge(problem, reverse_prob=reverse_prob)
