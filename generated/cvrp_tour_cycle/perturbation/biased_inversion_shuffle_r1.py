from random import Random

from generated.cvrp_tour_cycle.model.parts import canonical

COMPONENT = {
    "name": "biased_inversion_shuffle",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class BiasedInversionShuffle:
    def perturb(self, sol, strength: float, rng: Random):
        tour = list(canonical(sol))
        n = len(tour)
        if n < 2:
            return canonical(tuple(tour))

        # Strength controls how much of the tour is affected.
        span = max(2, min(n, int(round(2 + strength))))
        length = rng.randint(2, span)

        # Bias toward longer reversals as strength increases.
        start_max = n - length
        start = rng.randrange(0, start_max + 1)

        block = tour[start : start + length]
        if rng.random() < 0.5:
            block.reverse()
        else:
            rng.shuffle(block)

        # Ensure the move is not a no-op.
        if block == tour[start : start + length]:
            block = list(reversed(block))

        new_tour = tour[:start] + block + tour[start + length :]
        if tuple(new_tour) == tuple(tour):
            # Final safeguard: swap two positions inside the chosen block.
            i = start
            j = start + length - 1
            if i != j:
                new_tour[i], new_tour[j] = new_tour[j], new_tour[i]

        return canonical(tuple(new_tour))


def build_component(problem, **params):
    return BiasedInversionShuffle()
