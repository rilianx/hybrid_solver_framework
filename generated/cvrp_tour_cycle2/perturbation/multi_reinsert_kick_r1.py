from random import Random

COMPONENT = {
    "name": "multi_reinsert_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class MultiReinsertKick:
    def __init__(self, problem):
        self.problem = problem

    def perturb(self, sol, strength: float, rng: Random):
        parts = self.problem.parts
        tour = list(parts.canonical(sol))
        n = len(tour)
        if n < 2:
            return parts.canonical(tuple(tour))

        k = max(1, min(n - 1, int(round(strength))))
        work = tour[:]

        for _ in range(k):
            if len(work) < 2:
                break
            i = rng.randrange(len(work))
            c = work.pop(i)
            j = rng.randrange(len(work) + 1)
            work.insert(j, c)

        if tuple(work) == tuple(tour):
            # fallback: swap two positions
            i, j = rng.sample(range(n), 2)
            work[i], work[j] = work[j], work[i]

        return parts.canonical(tuple(work))


def build_component(problem, **params):
    params = dict(params)
    strength = float(params.get("strength", 3.0))
    if strength < 1.0:
        strength = 1.0
    if strength > 10.0:
        strength = 10.0
    return MultiReinsertKick(problem)
