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

        k = max(1, min(n, int(round(strength))))
        seg_len = max(2, min(n, int(round(self.reverse_fraction * k))))
        if seg_len > n:
            seg_len = n

        start = rng.randrange(0, n - seg_len + 1)
        segment = list(tour[start : start + seg_len])

        if len(segment) >= 2:
            # Distinct from relocation: scramble the internal order of a contiguous
            # segment instead of moving a block elsewhere.
            for i in range(len(segment) - 1, 0, -1):
                j = rng.randrange(0, i + 1)
                segment[i], segment[j] = segment[j], segment[i]

            if tuple(segment) == tour[start : start + seg_len]:
                # Guarantee a change when the shuffle accidentally leaves the segment unchanged.
                i = rng.randrange(0, len(segment))
                j = (i + 1) % len(segment)
                segment[i], segment[j] = segment[j], segment[i]

        perturbed = tour[:start] + tuple(segment) + tour[start + seg_len :]

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
