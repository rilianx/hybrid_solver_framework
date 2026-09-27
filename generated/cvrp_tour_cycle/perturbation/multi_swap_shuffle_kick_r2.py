from random import Random

COMPONENT = {
    "name": "multi_swap_shuffle_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "swap_ratio": {"type": "float", "range": [0.1, 1.0]},
    },
}


class MultiSwapShuffleKick:
    def __init__(self, swap_ratio: float = 0.4):
        self.swap_ratio = float(swap_ratio)

    def perturb(self, sol, strength: float, rng: Random):
        tour = tuple(sol)
        n = len(tour)
        if n <= 1:
            return tour

        # Use a contiguous segment inversion (2-opt style kick), which is
        # structurally different from block relocation / shuffle.
        k = max(2, min(n, int(round(strength))))
        seg_len = max(2, min(n, int(round(self.swap_ratio * k))))
        if seg_len >= n:
            i, j = 0, n
        else:
            i = rng.randrange(0, n - seg_len + 1)
            j = i + seg_len

        s = list(tour)
        s[i:j] = reversed(s[i:j])
        perturbed = tuple(s)

        if perturbed == tour:
            # Minimal fallback: swap two positions inside the chosen segment,
            # preserving the inversion-based nature of the kick.
            if n >= 2:
                a = i
                b = j - 1 if j - 1 != a else (a + 1) % n
                s = list(tour)
                s[a], s[b] = s[b], s[a]
                perturbed = tuple(s)

        return perturbed


def build_component(problem, **params):
    swap_ratio = params.get("swap_ratio", 0.4)
    return MultiSwapShuffleKick(swap_ratio=swap_ratio)
