from random import Random

COMPONENT = {
    "name": "double_bridge_tour_break",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class DoubleBridgeTourBreak:
    def __init__(self, problem):
        self.problem = problem

    def perturb(self, sol, strength: float, rng: Random):
        parts = self.problem.parts
        tour = list(parts.canonical(sol))
        n = len(tour)
        if n < 4:
            if n == 2:
                tour[0], tour[1] = tour[1], tour[0]
            elif n == 3:
                tour = [tour[1], tour[2], tour[0]]
            return parts.canonical(tuple(tour))

        # Pick three cut points to create a double-bridge style move.
        # Larger strength yields wider average segment sizes.
        max_seg = max(1, int(round(strength)))
        a = rng.randrange(1, max(2, n - 2))
        b = min(n - 2, a + rng.randint(1, max_seg))
        c = min(n - 1, b + rng.randint(1, max_seg))
        if not (1 <= a < b < c < n):
            a, b, c = sorted(rng.sample(range(1, n), 3))

        s1 = tour[:a]
        s2 = tour[a:b]
        s3 = tour[b:c]
        s4 = tour[c:]

        new_tour = s1 + s3 + s2 + s4
        if tuple(new_tour) == tuple(tour):
            # fallback: rotate a middle block
            new_tour = s1 + s4 + s2 + s3

        if tuple(new_tour) == tuple(tour):
            # final fallback: swap two random customers
            i, j = rng.sample(range(n), 2)
            new_tour = tour[:]
            new_tour[i], new_tour[j] = new_tour[j], new_tour[i]

        return parts.canonical(tuple(new_tour))


def build_component(problem, **params):
    params = dict(params)
    strength = float(params.get("strength", 4.0))
    if strength < 1.0:
        strength = 1.0
    if strength > 10.0:
        strength = 10.0
    return DoubleBridgeTourBreak(problem)
