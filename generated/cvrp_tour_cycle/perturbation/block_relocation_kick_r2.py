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

        # Block size increases mildly with strength, but the main effect of
        # strength is to push the relocated block farther from its origin.
        block_len = max(1, min(n - 1, int(round(strength / 2.0))))
        if block_len >= n:
            block_len = n - 1

        start = rng.randrange(0, n - block_len + 1)
        block = tour[start : start + block_len]
        remainder = tour[:start] + tour[start + block_len :]

        if not remainder:
            return self.canonical(tuple(tour))

        # Larger strength -> larger expected displacement from the original position.
        max_disp = len(remainder)
        disp = max(1, min(max_disp, int(round(strength))))

        # Choose a direction, then place the block at a distance proportional to strength.
        if rng.random() < 0.5:
            target = start + disp
        else:
            target = start - disp

        # Map the target from the original index space to the reduced tour.
        insert_pos = target
        if insert_pos < 0:
            insert_pos = 0
        if insert_pos > len(remainder):
            insert_pos = len(remainder)

        new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]

        if tuple(new_tour) == tuple(tour):
            # Deterministic fallback to guarantee a non-null move.
            if len(remainder) >= 1:
                insert_pos = (insert_pos + disp) % (len(remainder) + 1)
                new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]
            else:
                return self.canonical(tuple(tour))

        return self.canonical(tuple(new_tour))


def build_component(problem, **params):
    _ = params.get("strength", 3.0)
    return BlockRelocationKick(problem)
