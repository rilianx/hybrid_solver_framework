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
        if k == n:
            idxs = list(range(n))
        else:
            start = rng.randint(0, n - k)
            idxs = list(range(start, start + k))

        selected = [tour[i] for i in idxs]
        rng.shuffle(selected)

        new_tour = tour[:]
        for pos, val in zip(idxs, selected):
            new_tour[pos] = val

        if tuple(new_tour) == tuple(tour):
            # Ensure a different solution for strength >= 1.
            if len(idxs) >= 2:
                a, b = idxs[0], idxs[-1]
                new_tour[a], new_tour[b] = new_tour[b], new_tour[a]
            else:
                new_tour = tour[::-1]

        return self.canonical(tuple(new_tour))


def build_component(problem, strength: float = 4.0):
    return RandomThreeWayShuffleKick(problem)
