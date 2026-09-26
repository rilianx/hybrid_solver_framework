from random import Random

COMPONENT = {
    "name": "segment_reversal_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class SegmentReversalKick:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def perturb(self, sol, strength: float, rng: Random):
        tour = list(self.canonical(sol))
        n = len(tour)
        if n <= 1:
            return self.canonical(tuple(tour))

        span = max(2, min(n, int(round(strength)) + 1))
        a = rng.randrange(0, n - 1)
        b = min(n, a + span)
        if b - a < 2:
            a = 0
            b = n if n >= 2 else 1

        new_tour = tour[:a] + list(reversed(tour[a:b])) + tour[b:]
        if tuple(new_tour) == tuple(tour):
            i = rng.randrange(n)
            j = (i + 1) % n
            new_tour[i], new_tour[j] = new_tour[j], new_tour[i]

        return self.canonical(tuple(new_tour))


def build_component(problem, **params):
    _ = params.get("strength", 3.0)
    return SegmentReversalKick(problem)
