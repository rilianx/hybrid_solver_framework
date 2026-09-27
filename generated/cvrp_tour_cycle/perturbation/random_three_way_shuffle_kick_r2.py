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

        k = max(2, min(n, int(round(strength))))
        if k >= n:
            idxs = list(range(n))
            start = 0
        else:
            start = rng.randint(0, n - k)
            idxs = list(range(start, start + k))

        block = tour[start:start + k]

        if k == 2:
            block = [block[1], block[0]]
        else:
            shift = rng.randint(1, k - 1)
            block = block[shift:] + block[:shift]

        new_tour = tour[:]
        new_tour[start:start + k] = block

        if tuple(new_tour) == tuple(tour):
            if k >= 2:
                new_tour[start], new_tour[start + k - 1] = new_tour[start + k - 1], new_tour[start]
            else:
                new_tour = tour[::-1]

        return self.canonical(tuple(new_tour))


def build_component(problem, strength: float = 4.0):
    return RandomThreeWayShuffleKick(problem)
