from random import Random

from generated.jobshop_operations_cycle.model.parts import canonical

COMPONENT = {
    "name": "random_distinct_pair_swaps",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"max_retries": {"type": "int", "range": [5, 100]}},
}


def _force_diff(s, rng):
    n = len(s)
    if n < 2:
        return s
    for _ in range(50):
        i, j = rng.randrange(n), rng.randrange(n)
        if s[i] != s[j]:
            s[i], s[j] = s[j], s[i]
            return s
    for i in range(n - 1):
        if s[i] != s[i + 1]:
            s[i], s[i + 1] = s[i + 1], s[i]
            return s
    return s


class RandomDistinctPairSwaps:
    def __init__(self, max_retries=30):
        self.max_retries = int(max_retries)

    def perturb(self, sol, strength: float, rng: Random):
        base = canonical(sol)
        s = list(base)
        n = len(s)
        if n < 2:
            return base
        k = max(1, int(round(strength)))
        for _ in range(k):
            for _t in range(self.max_retries):
                i, j = rng.randrange(n), rng.randrange(n)
                if s[i] != s[j]:
                    s[i], s[j] = s[j], s[i]
                    break
        out = canonical(s)
        if out == base:
            out = canonical(_force_diff(s, rng))
        return out


def build_component(problem, max_retries=30):
    return RandomDistinctPairSwaps(max_retries=max_retries)
