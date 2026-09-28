from random import Random

COMPONENT = {
    "name": "block_relocation_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class BlockRelocationKick:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def perturb(self, sol, strength: float, rng: Random):
        tour = list(self.canonical(sol))
        n = len(tour)
        if n <= 1:
            return self.canonical(tuple(tour))

        # Keep the move elementary: relocate a single client.
        # The strength controls the maximum displacement of the insertion point,
        # so larger strength yields, on average, larger changes.
        block_len = 1

        start = rng.randrange(0, n)
        block = tour[start : start + block_len]
        remainder = tour[:start] + tour[start + block_len :]

        if not remainder:
            return self.canonical(tuple(tour))

        max_disp = max(1, min(len(remainder), int(round(strength))))
        disp = rng.randint(1, max_disp)

        if rng.random() < 0.5:
            target = start + disp
        else:
            target = start - disp

        # Convert from original index space to insertion position in the reduced tour.
        insert_pos = target
        if insert_pos < 0:
            insert_pos = 0
        elif insert_pos > len(remainder):
            insert_pos = len(remainder)

        new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]

        if tuple(new_tour) == tuple(tour):
            # Exact undo-safe fallback: move the single client to the nearest different position.
            if len(remainder) >= 1:
                insert_pos = (start + 1) % (len(remainder) + 1)
                new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]
            else:
                return self.canonical(tuple(tour))

        return self.canonical(tuple(new_tour))


def build_component(problem, **params):
    _ = params.get("strength", 3.0)
    return BlockRelocationKick(problem)
