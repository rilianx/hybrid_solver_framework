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

        # Strength controls how disruptive the move is:
        # - low strength: short block, reinsert nearby
        # - high strength: longer block, reinsert far away
        s = max(1.0, min(10.0, float(strength)))
        frac = (s - 1.0) / 9.0

        # Block length grows monotonically with strength.
        max_len = n - 1
        length = 1 + int(round(frac * (max_len - 1)))
        length = max(1, min(max_len, length))

        start = rng.randrange(0, n - length + 1)
        block = tour[start : start + length]
        remainder = tour[:start] + tour[start + length :]

        # Reinsert position:
        # small strengths sample from a tight neighborhood around the original
        # location; larger strengths sample from positions increasingly farther.
        rem_n = len(remainder)
        assert rem_n == n - length

        if rem_n == 0:
            return canonical(tuple(tour))

        # Original insertion position in the shortened tour:
        base_pos = start

        # Window radius grows with strength, capped by the available space.
        radius = int(round(frac * rem_n))
        if radius <= 0:
            radius = 1

        if s <= 2.5:
            # Local perturbation.
            lo = max(0, base_pos - radius)
            hi = min(rem_n, base_pos + radius)
            candidates = [p for p in range(lo, hi + 1) if p != base_pos]
            if not candidates:
                candidates = [p for p in range(rem_n + 1) if p != base_pos]
            insert_pos = rng.choice(candidates)
        else:
            # More disruptive perturbation: prefer positions far from the
            # original location, ensuring stronger kicks are larger on average.
            far_candidates = [
                p for p in range(rem_n + 1)
                if p != base_pos and abs(p - base_pos) >= max(1, radius // 2)
            ]
            if far_candidates:
                insert_pos = rng.choice(far_candidates)
            else:
                insert_pos = rng.randrange(0, rem_n + 1)
                if insert_pos == base_pos:
                    insert_pos = (insert_pos + 1) % (rem_n + 1)

        new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]

        # Guarantee a non-no-op move.
        if tuple(new_tour) == tuple(tour):
            if rem_n >= 1:
                insert_pos = (insert_pos + 1) % (rem_n + 1)
                if insert_pos == base_pos:
                    insert_pos = (insert_pos + 1) % (rem_n + 1)
                new_tour = remainder[:insert_pos] + block + remainder[insert_pos:]
            else:
                new_tour = list(reversed(tour))

        return canonical(tuple(new_tour))


def build_component(problem, **params):
    strength = params.get("strength", 3.0)
    return BiasedInversionShuffle()
