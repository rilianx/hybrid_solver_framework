from random import Random

COMPONENT = {
    "name": "random_three_way_shuffle_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 50.0]},
    },
}


class RandomThreeWayShuffleKick:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def perturb(self, sol, strength: float, rng: Random):
        tour = list(self.canonical(sol))
        n = len(tour)
        if n < 2:
            return self.canonical(tuple(tour))

        # Strength controls how many elementary shuffles are applied.
        # Larger strength => more disturbed solution, preserving monotonicity.
        steps = max(1, int(round(strength)))

        new_tour = tour[:]
        for _ in range(steps):
            if n < 2:
                break

            # Use a segment whose expected size grows with strength, capped by n.
            max_len = min(n, 2 + steps)
            k = rng.randint(2, max_len) if max_len >= 2 else 2

            start = 0 if k >= n else rng.randint(0, n - k)
            end = start + k
            block = new_tour[start:end]

            if k == 2:
                block = [block[1], block[0]]
            else:
                shift = rng.randint(1, k - 1)
                block = block[shift:] + block[:shift]

            new_tour[start:end] = block

        if tuple(new_tour) == tuple(tour) and n >= 2:
            new_tour[0], new_tour[-1] = new_tour[-1], new_tour[0]

        return self.canonical(tuple(new_tour))


def build_component(problem, strength: float = 4.0):
    return RandomThreeWayShuffleKick(problem)
