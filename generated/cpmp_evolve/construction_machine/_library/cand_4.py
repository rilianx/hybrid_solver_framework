COMPONENT = {'name': 'origin_large_bad_top_gap_v2', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_gap': {'type': 'int', 'range': [1, 100], 'default': 4}, 'min_unlocked_bad': {'type': 'int', 'range': [0, 100], 'default': 1}, 'min_destinations': {'type': 'int', 'range': [1, 1000], 'default': 1}, 'require_no_sorted_compatible_destination': {'type': 'bool', 'default': True}}}
from core.parts import origin_machine

class LargeBadTopGapOrigin:
    """Mueve desde pilas con tope muy mal puesto, sobre todo cuando solo conviene apartarlo a buffer."""
    name = 'large_bad_top_gap'

    def __init__(self, min_gap: int, min_unlocked_bad: int, min_destinations: int, require_no_sorted_compatible_destination: bool, prefer_fewer_destinations: bool):
        self.min_gap = int(min_gap)
        self.min_unlocked_bad = int(min_unlocked_bad)
        self.min_destinations = int(min_destinations)
        self.require_no_sorted_compatible_destination = bool(require_no_sorted_compatible_destination)
        self.prefer_fewer_destinations = bool(prefer_fewer_destinations)

    def init(self, partial):
        return None

    def update(self, partial, memory, action):
        return memory

    def _is_legal_destination(self, partial, so, sd):
        if sd == so:
            return False
        if partial.h(sd) >= partial.H:
            return False
        if partial.visited is not None and partial.after(so, sd) in partial.visited:
            return False
        return True

    def _destination_stats(self, partial, so, moved):
        total = 0
        sorted_compatible = 0
        for sd in range(partial.S):
            if not self._is_legal_destination(partial, so, sd):
                continue
            total += 1
            if partial.is_sorted_stack(sd) and moved <= partial.g(sd):
                sorted_compatible += 1
        return (total, sorted_compatible)

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
            destinations, sorted_compatible = self._destination_stats(partial, so, top)
            if destinations < self.min_destinations:
                continue
            if self.require_no_sorted_compatible_destination and sorted_compatible > 0:
                continue
            height = partial.h(so)
            if self.prefer_fewer_destinations:
                key = (destinations, -gap, -unlocked_bad, -height, so)
            else:
                key = (-gap, -unlocked_bad, destinations, -height, so)
            candidates.append((key, so))
        candidates.sort()
        return [so for _, so in candidates]

def build_component(problem, min_gap=4, min_unlocked_bad=1, min_destinations=1, require_no_sorted_compatible_destination=True, prefer_fewer_destinations=True):
    return origin_machine(problem, LargeBadTopGapOrigin(min_gap=min_gap, min_unlocked_bad=min_unlocked_bad, min_destinations=min_destinations, require_no_sorted_compatible_destination=require_no_sorted_compatible_destination, prefer_fewer_destinations=prefer_fewer_destinations))
