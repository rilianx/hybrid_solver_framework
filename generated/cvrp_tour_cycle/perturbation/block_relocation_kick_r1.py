from random import Random

COMPONENT = {
    "name": "block_relocation_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "max_block_fraction": {"type": "float", "range": [0.1, 0.9]},
    },
}


class BlockRelocationKick:
    def __init__(self, max_block_fraction: float = 0.35):
        self.max_block_fraction = float(max_block_fraction)

    def perturb(self, sol, strength: float, rng: Random):
        tour = tuple(sol)
        n = len(tour)
        if n <= 1:
            return tour

        k = max(1, min(n, int(round(strength))))
        block_len = max(1, min(n - 1, int(round(self.max_block_fraction * k))))
        start = rng.randrange(0, n - block_len + 1)
        block = tour[start : start + block_len]
        remainder = tour[:start] + tour[start + block_len :]

        insert_pos = rng.randrange(0, len(remainder) + 1)
        if insert_pos == start and len(remainder) > 0:
            insert_pos = (insert_pos + 1) % (len(remainder) + 1)

        perturbed = remainder[:insert_pos] + block + remainder[insert_pos:]
        if perturbed == tour:
            # Deterministic fallback to guarantee a different solution for strength >= 1
            if n >= 2:
                perturbed = (tour[1], tour[0]) + tour[2:]
        return tuple(perturbed)


def build_component(problem, **params):
    max_block_fraction = params.get("max_block_fraction", 0.35)
    return BlockRelocationKick(max_block_fraction=max_block_fraction)
