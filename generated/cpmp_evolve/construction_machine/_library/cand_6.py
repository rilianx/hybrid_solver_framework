COMPONENT = {'name': 'buffered_capped_misordered_source', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'max_compatible_dests': {'type': 'int', 'range': [0, 1000], 'default': 0}}}
from core.parts import origin_machine

class BufferedCappedMisorderedSource:
    """Mueve desde pilas cuyo tope está bien puesto pero tapa desorden y solo queda salida de buffer."""
    name = 'buffered_capped_misordered_source'

    def __init__(self, min_cover_gap, max_compatible_dests, min_total_dests, min_unlocked_bad_below, prefer_fewer_total_dests, prefer_more_cover_gap):
        self.min_cover_gap = int(min_cover_gap)
        self.max_compatible_dests = int(max_compatible_dests)
        self.min_total_dests = int(min_total_dests)
        self.min_unlocked_bad_below = int(min_unlocked_bad_below)
        self.prefer_fewer_total_dests = bool(prefer_fewer_total_dests)
        self.prefer_more_cover_gap = bool(prefer_more_cover_gap)

    def init(self, partial):
        return None

    def update(self, partial, memory, action):
        return memory

    def _destination_counts(self, partial, so, top):
        total_dests = 0
        compatible_dests = 0
        for sd in range(partial.S):
            if sd == so or partial.h(sd) >= partial.H:
                continue
            if partial.visited is not None and partial.after(so, sd) in partial.visited:
                continue
            total_dests += 1
            if partial.g(sd) >= top:
                compatible_dests += 1
        return (total_dests, compatible_dests)

    def sources(self, partial, memory):
        candidates = []
        for so in range(partial.S):
            height = partial.h(so)
            if height <= 1:
                continue
            if partial.is_sorted_stack(so):
                continue
            sorted_prefix = partial.sorted_n[so]
            if sorted_prefix >= height - 1:
                continue
            stack = partial.stacks[so]
            top = stack[-1]
            below = stack[-2]
            if below < top:
                continue
            cover_gap = below - top
            if cover_gap < self.min_cover_gap:
                continue
            unlocked_bad_below = partial.ub(so)
            if unlocked_bad_below < self.min_unlocked_bad_below:
                continue
            total_dests, compatible_dests = self._destination_counts(partial, so, top)
            if total_dests < self.min_total_dests:
                continue
            if compatible_dests > self.max_compatible_dests:
                continue
            if self.prefer_more_cover_gap:
                gap_key = -cover_gap
            else:
                gap_key = cover_gap
            if self.prefer_fewer_total_dests:
                total_key = total_dests
            else:
                total_key = -total_dests
            key = (compatible_dests, total_key, gap_key, -unlocked_bad_below, -height, so)
            candidates.append((key, so))
        candidates.sort()
        return [so for _, so in candidates]

def build_component(problem, min_cover_gap=0, max_compatible_dests=0, min_total_dests=1, min_unlocked_bad_below=1, prefer_fewer_total_dests=True, prefer_more_cover_gap=True):
    return origin_machine(problem, BufferedCappedMisorderedSource(min_cover_gap=min_cover_gap, max_compatible_dests=max_compatible_dests, min_total_dests=min_total_dests, min_unlocked_bad_below=min_unlocked_bad_below, prefer_fewer_total_dests=prefer_fewer_total_dests, prefer_more_cover_gap=prefer_more_cover_gap))
