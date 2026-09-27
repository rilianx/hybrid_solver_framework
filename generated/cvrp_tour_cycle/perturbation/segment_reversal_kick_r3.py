from random import Random

COMPONENT = {
    "name": "segment_reversal_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "reverse_fraction": {"type": "float", "range": [0.1, 1.0]},
    },
}


class SegmentReversalKick:
    def __init__(self, reverse_fraction: float = 0.5):
        self.reverse_fraction = float(reverse_fraction)

    def perturb(self, sol, strength: float, rng: Random):
        tour = tuple(sol)
        n = len(tour)
        if n <= 1:
            return tour

        # Double-bridge style kick on the grand tour:
        # split the sequence into 4 consecutive pieces and reconnect them
        # in a different order, which is qualitatively different from
        # relocating a single block or shuffling within one segment.
        max_span = max(1, min(n - 1, int(round(self.reverse_fraction * max(1.0, float(strength))))))
        if n < 4 or max_span < 2:
            i = rng.randrange(0, n)
            j = (i + 1) % n
            s = list(tour)
            s[i], s[j] = s[j], s[i]
            return tuple(s)

        # Pick two internal cut points; derive two outer cuts to form 4 pieces.
        a = rng.randrange(1, n - 2)
        b = rng.randrange(a + 1, n - 1)

        # Encourage a nontrivial middle-span while keeping the operator simple.
        if b - a > max_span:
            b = a + max_span

        # 4 segments: [0:a], [a:b], [b:n]
        # Reconnection with an internal reversal of the middle part gives
        # a kick that changes adjacency structure more broadly than relocation.
        s1 = tour[:a]
        s2 = tour[a:b]
        s3 = tour[b:]

        perturbed = s1 + tuple(reversed(s2)) + s3

        if perturbed == tour:
            # Fallback: perform a classical double-bridge on a 4-way split.
            p = rng.randrange(1, max(2, n - 2))
            q = rng.randrange(p + 1, n - 1)
            r = rng.randrange(q + 1, n)
            perturbed = tour[:p] + tour[q:r] + tour[p:q] + tour[r:]

        if perturbed == tour:
            i = rng.randrange(0, n)
            j = (i + 1) % n
            s = list(tour)
            s[i], s[j] = s[j], s[i]
            perturbed = tuple(s)

        return perturbed


def build_component(problem, **params):
    reverse_fraction = params.get("reverse_fraction", 0.5)
    return SegmentReversalKick(reverse_fraction=reverse_fraction)
