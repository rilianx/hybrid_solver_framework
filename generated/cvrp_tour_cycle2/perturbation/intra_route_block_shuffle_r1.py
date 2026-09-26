from random import Random

COMPONENT = {
    "name": "intra_route_block_shuffle",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class IntraRouteBlockShuffle:
    def __init__(self, problem):
        self.problem = problem

    def perturb(self, sol, strength: float, rng: Random):
        parts = self.problem.parts
        tour = list(parts.canonical(sol))
        n = len(tour)
        if n < 2:
            return parts.canonical(tuple(tour))

        k = max(2, min(n, int(round(strength))))
        block_len = min(n, max(2, k))
        start = rng.randrange(0, n - block_len + 1)
        block = tour[start : start + block_len]
        rng.shuffle(block)

        new_tour = tour[:start] + block + tour[start + block_len :]
        if tuple(new_tour) == tuple(tour):
            # deterministic fallback: reverse the block
            block = list(reversed(block))
            new_tour = tour[:start] + block + tour[start + block_len :]
        return parts.canonical(tuple(new_tour))


def build_component(problem, **params):
    params = dict(params)
    strength = float(params.get("strength", 3.0))
    if strength < 1.0:
        strength = 1.0
    if strength > 10.0:
        strength = 10.0
    return IntraRouteBlockShuffle(problem)
