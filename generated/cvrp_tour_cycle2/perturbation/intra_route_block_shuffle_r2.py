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

        # Stronger kicks act on longer contiguous blocks, which makes the
        # expected distance monotone with respect to `strength`.
        block_len = 2 + int((s - 1.0) * (n - 2) / 9.0)
        block_len = max(2, min(n, block_len))

        start = rng.randrange(0, n - block_len + 1)
        block = tour[start : start + block_len]

        if block_len == 2:
            # Elementary move: swap the two elements.
            block = [block[1], block[0]]
        else:
            # A single cyclic shift of the selected block; the shift grows with
            # the requested strength to ensure monotonicity.
            shift = 1 + int((s - 1.0) * (block_len - 2) / 9.0)
            shift = max(1, min(block_len - 1, shift))
            block = block[shift:] + block[:shift]

            if tuple(block) == tuple(tour[start : start + block_len]):
                # Deterministic fallback that still changes the block.
                block = [block[-1]] + block[:-1]

        new_tour = tour[:start] + block + tour[start + block_len :]
        return parts.canonical(tuple(new_tour))


def build_component(problem, **params):
    return IntraRouteBlockShuffle(problem)
