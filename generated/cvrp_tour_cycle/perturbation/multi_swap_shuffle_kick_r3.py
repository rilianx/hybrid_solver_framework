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

        # Perturb a dispersed subset of positions with a cyclic reassignment.
        # This differs from block relocation/reversal by touching non-contiguous
        # variables and changing their values through a multi-cycle shuffle.
        k = max(2, min(n, int(round(self.swap_ratio * strength))))
        if k >= n:
            idxs = list(range(n))
        else:
            idxs = sorted(rng.sample(range(n), k))

        s = list(tour)
        values = [s[i] for i in idxs]

        # Create a nontrivial cyclic shift of the selected values.
        shift = rng.randrange(1, k) if k > 1 else 0
        shifted = values[shift:] + values[:shift]

        # Apply the reassignment.
        for pos, val in zip(idxs, shifted):
            s[pos] = val

        perturbed = tuple(s)
        if perturbed == tour and k >= 2:
            # Fallback: swap two dispersed positions.
            a, b = idxs[0], idxs[-1]
            if a != b:
                s = list(tour)
                s[a], s[b] = s[b], s[a]
                perturbed = tuple(s)

        return perturbed


def build_component(problem, **params):
    swap_ratio = params.get("swap_ratio", 0.4)
    return MultiSwapShuffleKick(swap_ratio=swap_ratio)
