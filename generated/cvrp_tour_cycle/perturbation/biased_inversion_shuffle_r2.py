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

        # Use a single-segment relocation perturbation:
        # remove one contiguous block and reinsert it elsewhere.
        # This is structurally different from a double-bridge kick.
        max_len = min(n - 1, max(2, int(round(1 + strength))))
        length = rng.randint(1, max_len)

        start = rng.randrange(0, n - length + 1)
        block = tour[start : start + length]
        remainder = tour[:start] + tour[start + length :]

        # Insert the extracted block at a different position in the remainder.
        # Positions are relative to the shortened tour.
        insert_pos = rng.randrange(0, len(remainder) + 1)
        if insert_pos == start:
            insert_pos = (insert_pos + 1) % (len(remainder) + 1)

        new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]

        # Ensure the perturbation is not a no-op.
        if tuple(new_tour) == tuple(tour):
            if n >= 3:
                # Deterministically change the insertion point when possible.
                insert_pos = (insert_pos + 1) % (len(remainder) + 1)
                if insert_pos == start:
                    insert_pos = (insert_pos + 1) % (len(remainder) + 1)
                new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]
            else:
                new_tour = list(reversed(tour))

        return canonical(tuple(new_tour))


def build_component(problem, **params):
    return BiasedInversionShuffle()
