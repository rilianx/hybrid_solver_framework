from random import Random

COMPONENT = {
    "name": "segment_relocation_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 50.0]},
    },
}


class SegmentRelocationKick:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def perturb(self, sol, strength: float, rng: Random):
        tour = list(self.canonical(sol))
        n = len(tour)
        if n < 2:
            return self.canonical(tuple(tour))

        block_len = max(1, min(n - 1, int(round(strength))))
        start = rng.randint(0, n - block_len)
        block = tour[start : start + block_len]
        remainder = tour[:start] + tour[start + block_len :]

        insert_pos = rng.randint(0, len(remainder))
        new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]

        if tuple(new_tour) == tuple(tour):
            # Force a change with a minimal relocation.
            if n >= 3:
                i = rng.randint(0, n - 2)
                j = rng.randint(i + 1, n - 1)
                block = tour[i : j + 1]
                remainder = tour[:i] + tour[j + 1 :]
                insert_pos = rng.randint(0, len(remainder))
                new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]
            else:
                new_tour = tour[::-1]

        return self.canonical(tuple(new_tour))


def build_component(problem, strength: float = 3.0):
    return SegmentRelocationKick(problem)
