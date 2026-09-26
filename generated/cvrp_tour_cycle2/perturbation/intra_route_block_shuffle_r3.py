from random import Random

COMPONENT = {
    "name": "intra_route_block_shuffle",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class IntraRouteBlockShuffle:
    def __init__(self, problem):
        self.problem = problem

    def perturb(self, sol, strength: float, rng: Random):
        parts = self.problem.parts
        tour = list(parts.canonical(sol))
        n = len(tour)
        if n < 2:
            return parts.canonical(tuple(tour))

        s = max(1.0, min(10.0, float(strength)))

        # Perturbation based on shuffling a contiguous block of the grand tour.
        # Stronger kicks use longer blocks, but the move remains a single
        # elementary block permutation (not a tour cut / bridge move).
        block_len = 2 + int((s - 1.0) * (n - 2) / 9.0)
        block_len = max(2, min(n, block_len))

        start = rng.randrange(0, n - block_len + 1)
        block = tour[start : start + block_len]

        if block_len == 2:
            # Elementary swap for the smallest possible block.
            block = [block[1], block[0]]
        else:
            original = tuple(block)
            # Shuffle the selected block in-place using the provided RNG.
            # Retry a few times to avoid returning the same arrangement.
            for _ in range(8):
                rng.shuffle(block)
                if tuple(block) != original:
                    break
            else:
                # Deterministic fallback: cyclic rotation by one position.
                block = block[1:] + block[:1]

        new_tour = tour[:start] + block + tour[start + block_len :]
        return parts.canonical(tuple(new_tour))


def build_component(problem, **params):
    return IntraRouteBlockShuffle(problem)
