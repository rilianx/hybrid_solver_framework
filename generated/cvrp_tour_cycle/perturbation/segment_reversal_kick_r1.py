from random import Random

COMPONENT = {
    "name": "segment_reversal_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 50.0]},
    },
}


class SegmentReversalKick:
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
            i, j = 0, n
        else:
            i = rng.randint(0, n - k)
            j = i + k

        segment = tour[i:j]
        segment.reverse()
        new_tour = tour[:i] + segment + tour[j:]
        return self.canonical(tuple(new_tour))


def build_component(problem, strength: float = 3.0):
    return SegmentReversalKick(problem)
