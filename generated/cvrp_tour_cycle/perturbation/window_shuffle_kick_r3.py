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

        # Window length grows with strength to make the perturbation strictly stronger.
        block_len = max(1, min(n - 1, int(round(strength))))
        if block_len >= n:
            block_len = n - 1

        start = rng.randrange(0, n - block_len + 1)
        end = start + block_len
        block = tour[start:end]
        remainder = tour[:start] + tour[end:]

        if not remainder:
            return self.canonical(tuple(tour))

        # For weak kicks, insert the block at a random position.
        # For stronger kicks, push it to the opposite side to increase disruption.
        if strength < 2.5:
            insert_pos = rng.randrange(0, len(remainder) + 1)
        else:
            # Far-end relocation makes the average distance grow with strength.
            insert_pos = 0 if start >= n // 2 else len(remainder)

        new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]

        if tuple(new_tour) == tuple(tour):
            if len(remainder) >= 2:
                insert_pos = 0 if insert_pos != 0 else len(remainder)
                new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]
            else:
                new_tour = [tour[1], tour[0]]

        return self.canonical(tuple(new_tour))


def build_component(problem, **params):
    _ = params.get("strength", 3.0)
    return WindowShuffleKick(problem)
