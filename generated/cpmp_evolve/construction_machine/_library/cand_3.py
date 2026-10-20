COMPONENT = {'name': 'origin_small_bad_top_gap', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'max_gap': {'type': 'int', 'range': [1, 100], 'default': 3}, 'min_destinations': {'type': 'int', 'range': [1, 1000], 'default': 1}}}
from core.parts import origin_machine

class SmallBadTopGapOrigin:
    """Mueve desde pilas cuyo tope está mal puesto pero solo por una brecha pequeña."""
    name = 'small_bad_top_gap'

    def __init__(self, max_gap: int, min_destinations: int, prefer_fewer_destinations: bool):
        self.max_gap = int(max_gap)
        self.min_destinations = int(min_destinations)
        self.prefer_fewer_destinations = bool(prefer_fewer_destinations)

    def init(self, partial):
        return None

    def update(self, partial, memory, action):
        return memory

    def _count_destinations(self, partial, so):
        count = 0
        for sd in range(partial.S):
            if sd == so or partial.h(sd) >= partial.H:
                continue
            if partial.visited is not None and partial.after(so, sd) in partial.visited:
                continue
            count += 1
        return count

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
            if gap > self.max_gap:
                continue
            destinations = self._count_destinations(partial, so)
            if destinations < self.min_destinations:
                continue
            height = partial.h(so)
            unlocked_bad = partial.ub(so)
            if self.prefer_fewer_destinations:
                key = (destinations, -gap, -unlocked_bad, -height, so)
            else:
                key = (-gap, -unlocked_bad, -height, destinations, so)
            candidates.append((key, so))
        candidates.sort()
        return [so for _, so in candidates]

def build_component(problem, max_gap=3, min_destinations=1, prefer_fewer_destinations=True):
    return origin_machine(problem, SmallBadTopGapOrigin(max_gap=max_gap, min_destinations=min_destinations, prefer_fewer_destinations=prefer_fewer_destinations))
