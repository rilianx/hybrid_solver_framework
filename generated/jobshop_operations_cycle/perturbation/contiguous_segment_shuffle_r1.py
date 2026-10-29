from random import Random

from generated.jobshop_operations_cycle.model.parts import canonical

COMPONENT = {
    "name": "contiguous_segment_shuffle",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "segment_scale": {"type": "float", "range": [1.0, 4.0]},
        "max_retries": {"type": "int", "range": [3, 50]},
    },
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


class ContiguousSegmentShuffle:
    def __init__(self, segment_scale=2.0, max_retries=10):
        self.segment_scale = float(segment_scale)
        self.max_retries = int(max_retries)

    def perturb(self, sol, strength: float, rng: Random):
        base = canonical(sol)
        n = len(base)
        if n < 2:
            return base
        L = int(round(max(1.0, strength) * self.segment_scale)) + 1
        L = max(2, min(n, L))
        for _ in range(self.max_retries):
            a = rng.randrange(0, n - L + 1)
            seg = list(base[a:a + L])
            if len(set(seg)) < 2:
                continue
            rng.shuffle(seg)
            s = list(base[:a]) + seg + list(base[a + L:])
            out = canonical(s)
            if out != base:
                return out
        return canonical(_force_diff(list(base), rng))


def build_component(problem, segment_scale=2.0, max_retries=10):
    return ContiguousSegmentShuffle(segment_scale=segment_scale, max_retries=max_retries)
