COMPONENT = {'name': 'origin_large_bad_top_gap', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_gap': {'type': 'int', 'range': [1, 100], 'default': 5}, 'max_compatible_destinations': {'type': 'int', 'range': [0, 1000], 'default': 1}, 'min_total_destinations': {'type': 'int', 'range': [1, 1000], 'default': 1}, 'min_unlocked_bad': {'type': 'int', 'range': [0, 1000], 'default': 1}}}
from core.parts import origin_machine

class LargeBadTopGapOrigin:
    """Mueve desde pilas con tope muy mal puesto y con muy pocos apoyos compatibles factibles."""
    name = 'large_bad_top_gap'

    def __init__(self, min_gap: int, max_compatible_destinations: int, min_total_destinations: int, min_unlocked_bad: int, prefer_zero_compatible_first: bool, prefer_more_gap: bool):
        self.min_gap = int(min_gap)
        self.max_compatible_destinations = int(max_compatible_destinations)
        self.min_total_destinations = int(min_total_destinations)
        self.min_unlocked_bad = int(min_unlocked_bad)
        self.prefer_zero_compatible_first = bool(prefer_zero_compatible_first)
        self.prefer_more_gap = bool(prefer_more_gap)

    def init(self, partial):
        return None

    def update(self, partial, memory, action):
        return memory

    def _destination_counts(self, partial, so):
        stack = partial.stacks[so]
        moved = stack[-1]
        total_count = 0
        compatible_count = 0
        for sd in range(partial.S):
            if sd == so or partial.h(sd) >= partial.H:
                continue
            if partial.visited is not None and partial.after(so, sd) in partial.visited:
                continue
            total_count += 1
            if moved <= partial.g(sd):
                compatible_count += 1
        return (total_count, compatible_count)

    def sources(self, partial, memory):
        candidates = []
        for so in range(partial.S):
            if partial.h(so) < 2:
                continue
            stack = partial.stacks[so]
            top = stack[-1]
            below = stack[-2]
            if top <= below:
                continue
            gap = top - below
            if gap < self.min_gap:
                continue
            unlocked_bad = partial.ub(so)
            if unlocked_bad < self.min_unlocked_bad:
                continue
            total_destinations, compatible_destinations = self._destination_counts(partial, so)
            if total_destinations < self.min_total_destinations:
                continue
            if compatible_destinations > self.max_compatible_destinations:
                continue
            height = partial.h(so)
            sorted_prefix_after_pop = partial.sorted_n[so] >= height - 1
            zero_compatible_flag = compatible_destinations != 0 if self.prefer_zero_compatible_first else False
            gap_key = -gap if self.prefer_more_gap else gap
            key = (zero_compatible_flag, compatible_destinations, gap_key, -unlocked_bad, not sorted_prefix_after_pop, -height, so)
            candidates.append((key, so))
        candidates.sort()
        return [so for _, so in candidates]

def build_component(problem, min_gap=5, max_compatible_destinations=1, min_total_destinations=1, min_unlocked_bad=1, prefer_zero_compatible_first=True, prefer_more_gap=True):
    return origin_machine(problem, LargeBadTopGapOrigin(min_gap=min_gap, max_compatible_destinations=max_compatible_destinations, min_total_destinations=min_total_destinations, min_unlocked_bad=min_unlocked_bad, prefer_zero_compatible_first=prefer_zero_compatible_first, prefer_more_gap=prefer_more_gap))
