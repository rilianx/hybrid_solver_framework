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

        # Larger strength -> larger expected moved segment.
        max_len = max(1, min(n - 1, int(round(1.0 + (strength - 1.0) * (n - 2) / 9.0))))
        seg_len = rng.randint(1, max_len)

        start = rng.randrange(0, n - seg_len + 1)
        segment = tour[start : start + seg_len]
        remainder = tour[:start] + tour[start + seg_len :]

        if not remainder:
            return canonical(tuple(tour))

        m = len(remainder)

        # Larger strength -> choose reinsertion positions farther from the original location.
        min_dist = min(m, max(1, int(round(strength))))
        candidates = [pos for pos in range(m + 1) if pos != start and abs(pos - start) >= min_dist]

        if not candidates:
            candidates = [pos for pos in range(m + 1) if pos != start]
        if not candidates:
            return canonical(tuple(tour))

        insert_pos = rng.choice(candidates)
        new_tour = remainder[:insert_pos] + segment + remainder[insert_pos:]
        return canonical(tuple(new_tour))


def build_component(problem, **params):
    strength = params.get("strength", 3.0)
    return RandomSegmentRelocation()
