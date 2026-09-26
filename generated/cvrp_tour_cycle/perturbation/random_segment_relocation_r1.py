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

        max_len = max(1, min(n - 1, int(round(strength))))
        seg_len = rng.randint(1, max_len)

        start = rng.randrange(0, n - seg_len + 1)
        segment = tour[start : start + seg_len]
        remainder = tour[:start] + tour[start + seg_len :]

        if not remainder:
            return canonical(tuple(tour))

        insert_pos = rng.randrange(0, len(remainder) + 1)
        # Avoid the identity move when the segment is reinserted exactly where it was.
        if insert_pos == start:
            insert_pos = (insert_pos + 1) % (len(remainder) + 1)

        new_tour = remainder[:insert_pos] + segment + remainder[insert_pos:]
        return canonical(tuple(new_tour))


def build_component(problem, **params):
    return RandomSegmentRelocation()
