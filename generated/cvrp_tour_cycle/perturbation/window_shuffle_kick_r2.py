from random import Random

COMPONENT = {
    "name": "window_shuffle_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class WindowShuffleKick:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def perturb(self, sol, strength: float, rng: Random):
        tour = list(self.canonical(sol))
        n = len(tour)
        if n <= 1:
            return self.canonical(tuple(tour))

        # Select a contiguous block whose size depends on strength, then relocate it
        # to a different position. This is distinct from reversing/shuffling the block:
        # the internal order is preserved, but the block is removed and reinserted.
        block_len = max(1, min(n - 1, int(round(strength)) + 1))
        if block_len >= n:
            block_len = n - 1

        start = rng.randrange(0, n - block_len + 1)
        end = start + block_len
        block = tour[start:end]
        remainder = tour[:start] + tour[end:]

        if not remainder:
            return self.canonical(tuple(tour))

        insert_pos = rng.randrange(0, len(remainder) + 1)
        new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]

        # If the relocation accidentally yields the same ordering, force a
        # different cut/insert that moves the block elsewhere.
        if tuple(new_tour) == tuple(tour):
            if len(remainder) >= 2:
                insert_pos = (insert_pos + 1) % (len(remainder) + 1)
                new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]
            else:
                # n == 2: swap the two elements.
                new_tour = [tour[1], tour[0]]

        return self.canonical(tuple(new_tour))


def build_component(problem, **params):
    _ = params.get("strength", 3.0)
    return WindowShuffleKick(problem)
