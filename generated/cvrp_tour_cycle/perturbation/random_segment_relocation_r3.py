from random import Random

from generated.cvrp_tour_cycle.model.parts import canonical

COMPONENT = {
    "name": "random_segment_relocation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class RandomSegmentRelocation:
    def perturb(self, sol, strength: float, rng: Random):
        tour = list(canonical(sol))
        n = len(tour)
        if n < 2:
            return canonical(tuple(tour))

        strength = max(1.0, min(10.0, float(strength)))

        # Larger strength -> longer expected segment.
        max_len = max(1, min(n - 1, int(round(1.0 + (strength - 1.0) * (n - 2) / 9.0))))
        seg_len = rng.randint(1, max_len)

        start = rng.randrange(0, n - seg_len + 1)
        segment = tour[start : start + seg_len]
        remainder = tour[:start] + tour[start + seg_len :]
        m = len(remainder)
        if m == 0:
            return canonical(tuple(tour))

        # Larger strength -> insertion positions farther from the original location.
        # We rank candidate insertion positions by their distance from the original cut.
        # For low strength we allow only nearby reinsertion; for high strength we
        # progressively expand the set of admissible distant positions.
        candidates = [pos for pos in range(m + 1) if pos != start]
        if not candidates:
            return canonical(tuple(tour))

        distances = sorted({abs(pos - start) for pos in candidates})
        # Pick a minimum required distance based on strength; this is monotone with strength.
        # At strength=1 we accept the nearest possible moves, while at strength=10 we
        # restrict to the farthest positions whenever possible.
        idx = int(round((strength - 1.0) * (len(distances) - 1) / 9.0))
        min_dist = distances[idx]

        far_candidates = [pos for pos in candidates if abs(pos - start) >= min_dist]
        if not far_candidates:
            far_candidates = candidates

        insert_pos = rng.choice(far_candidates)
        new_tour = remainder[:insert_pos] + segment + remainder[insert_pos:]
        return canonical(tuple(new_tour))


def build_component(problem, **params):
    _ = problem
    strength = params.get("strength", 3.0)
    return RandomSegmentRelocation()
