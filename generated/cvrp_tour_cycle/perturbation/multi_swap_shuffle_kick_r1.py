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

        k = max(1, min(n, int(round(strength))))
        m = max(2, min(n, int(round(self.swap_ratio * k))))
        positions = rng.sample(range(n), m)

        values = [tour[i] for i in positions]
        rng.shuffle(values)

        s = list(tour)
        for pos, val in zip(positions, values):
            s[pos] = val

        perturbed = tuple(s)
        if perturbed == tour:
            # Fallback: perform a simple transposition to ensure a different solution.
            i = rng.randrange(0, n)
            j = (i + max(1, k)) % n
            s = list(tour)
            s[i], s[j] = s[j], s[i]
            perturbed = tuple(s)

        return perturbed


def build_component(problem, **params):
    swap_ratio = params.get("swap_ratio", 0.4)
    return MultiSwapShuffleKick(swap_ratio=swap_ratio)
