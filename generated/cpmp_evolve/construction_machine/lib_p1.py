COMPONENT = {'name': 'capped_misordered_source', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_cover_gap': {'type': 'int', 'range': [0, 1000000], 'default': 0}, 'min_compatible_dests': {'type': 'int', 'range': [1, 1000], 'default': 1}}}
from core.parts import origin_machine

class CappedMisorderedSource:
    """Mueve desde pilas con tope bien puesto que tapa desorden por debajo."""
    name = 'capped_misordered_source'

    def __init__(self, min_cover_gap, min_compatible_dests, prefer_fewer_dests):
        self.min_cover_gap = min_cover_gap
        self.min_compatible_dests = min_compatible_dests
        self.prefer_fewer_dests = prefer_fewer_dests

    def sources(self, partial, memory):
        candidates = []
        stacks = partial.stacks
        total_stacks = partial.S
        for so in range(total_stacks):
            height = partial.h(so)
            if height <= 1:
                continue
            if partial.is_sorted_stack(so):
                continue
            sorted_prefix = partial.sorted_n[so]
            if sorted_prefix >= height:
                continue
            top = stacks[so][-1]
            below = stacks[so][-2]
            if below < top:
                continue
            if sorted_prefix >= height - 1:
                continue
            cover_gap = below - top
            if cover_gap < self.min_cover_gap:
                continue
            compatible_dests = 0
            for sd in range(total_stacks):
                if sd == so or partial.h(sd) >= partial.H:
                    continue
                if partial.g(sd) < top:
                    continue
                if partial.visited is not None and partial.after(so, sd) in partial.visited:
                    continue
                compatible_dests += 1
            if compatible_dests < self.min_compatible_dests:
                continue
            if self.prefer_fewer_dests:
                key = (-cover_gap, compatible_dests, -height, so)
            else:
                key = (-cover_gap, -height, compatible_dests, so)
            candidates.append((key, so))
        candidates.sort()
        return [so for _, so in candidates]

def build_component(problem, min_cover_gap=0, min_compatible_dests=1, prefer_fewer_dests=True):
    return origin_machine(problem, CappedMisorderedSource(min_cover_gap=min_cover_gap, min_compatible_dests=min_compatible_dests, prefer_fewer_dests=prefer_fewer_dests))
