from random import Random

COMPONENT = {
    "name": "block_relocation_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class BlockRelocationKick:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def perturb(self, sol, strength: float, rng: Random):
        tour = list(self.canonical(sol))
        n = len(tour)
        if n <= 1:
            return self.canonical(tuple(tour))

        block_len = max(1, min(n - 1, int(round(strength))))
        if block_len >= n:
            block_len = n - 1

        start = rng.randrange(0, n - block_len + 1)
        block = tour[start:start + block_len]
        remainder = tour[:start] + tour[start + block_len:]

        if not remainder:
            return self.canonical(tuple(tour))

        insert_pos = rng.randrange(0, len(remainder) + 1)
        new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]

        if tuple(new_tour) == tuple(tour):
            # Force a different relocation if the random choice was null.
            if len(remainder) >= 2:
                insert_pos = (insert_pos + 1) % (len(remainder) + 1)
                new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]
            else:
                new_tour = list(reversed(tour))

        return self.canonical(tuple(new_tour))


def build_component(problem, **params):
    _ = params.get("strength", 3.0)
    return BlockRelocationKick(problem)
