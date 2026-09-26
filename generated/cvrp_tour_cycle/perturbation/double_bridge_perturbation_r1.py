from random import Random

from generated.cvrp_tour_cycle.model.parts import canonical

COMPONENT = {
    "name": "double_bridge_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class DoubleBridgePerturbation:
    def perturb(self, sol, strength: float, rng: Random):
        tour = list(canonical(sol))
        n = len(tour)
        if n < 4:
            # Fallback to a non-trivial rotation or swap when the tour is too short.
            if n == 2:
                tour[0], tour[1] = tour[1], tour[0]
                return canonical(tuple(tour))
            if n == 3:
                i = rng.randrange(3)
                j = (i + 1) % 3
                tour[i], tour[j] = tour[j], tour[i]
                return canonical(tuple(tour))
            return canonical(tuple(tour))

        # Choose three cut points, shaped by strength through a small number of tries.
        max_tries = max(1, int(round(strength)))
        for _ in range(max_tries):
            a = rng.randint(1, n - 3)
            b = rng.randint(a + 1, n - 2)
            c = rng.randint(b + 1, n - 1)

            p1 = tour[:a]
            p2 = tour[a:b]
            p3 = tour[b:c]
            p4 = tour[c:]

            # Classical double-bridge style recombination.
            new_tour = p1 + p3 + p2 + p4
            if tuple(new_tour) != tuple(tour):
                return canonical(tuple(new_tour))

        # Guaranteed fallback: reverse a randomly chosen block.
        i = rng.randrange(0, n - 1)
        j = rng.randrange(i + 1, n)
        tour[i : j + 1] = reversed(tour[i : j + 1])
        return canonical(tuple(tour))


def build_component(problem, **params):
    return DoubleBridgePerturbation()
