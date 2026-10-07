COMPONENT = {'name': 'buffer_aware_bad_top_placement', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'prefer_sorted_when_source_good': {'type': 'bool', 'default': True}, 'prefer_taller_support_for_compatible': {'type': 'bool', 'default': True}, 'prefer_buffer_for_capped_misordered': {'type': 'bool', 'default': True}, 'min_cover_gap_for_buffer_preference': {'type': 'int', 'range': [0, 100], 'default': 2}, 'prefer_smaller_incompatible_gap': {'type': 'bool', 'default': True}}}
from core.parts import placement_machine

class BufferAwareBadTopPlacement:
    """Ordena destinos distinguiendo topes malos y, si el tope tapa desorden, favorece buffers con menor violación."""
    name = 'buffer_aware_bad_top_placement'

    def __init__(self, prefer_sorted_when_source_good: bool, prefer_taller_support_for_compatible: bool, prefer_short_buffer_for_incompatible: bool, prefer_buffer_for_capped_misordered: bool, min_cover_gap_for_buffer_preference: int, prefer_smaller_incompatible_gap: bool):
        self.prefer_sorted_when_source_good = bool(prefer_sorted_when_source_good)
        self.prefer_taller_support_for_compatible = bool(prefer_taller_support_for_compatible)
        self.prefer_short_buffer_for_incompatible = bool(prefer_short_buffer_for_incompatible)
        self.prefer_buffer_for_capped_misordered = bool(prefer_buffer_for_capped_misordered)
        self.min_cover_gap_for_buffer_preference = int(min_cover_gap_for_buffer_preference)
        self.prefer_smaller_incompatible_gap = bool(prefer_smaller_incompatible_gap)

    def rank(self, partial, action):
        so = action.so
        sd = action.sd
        source_stack = partial.stacks[so]
        moved = source_stack[-1]
        source_height = partial.h(so)
        below = source_stack[-2] if source_height >= 2 else partial.G
        source_top_is_bad = source_height >= 2 and moved > below
        source_unsorted_below = not partial.is_sorted_stack(so) and partial.sorted_n[so] < source_height - 1
        source_capped_misordered = not source_top_is_bad and source_unsorted_below
        cover_gap = below - moved if source_capped_misordered else 0
        dest_top = partial.g(sd)
        compatible = moved <= dest_top
        dest_sorted = partial.is_sorted_stack(sd)
        dest_height = partial.h(sd)
        dest_sorted_n = partial.sorted_n[sd]
        incompatible_gap = moved - dest_top
        if self.prefer_smaller_incompatible_gap:
            incompatible_gap_key = incompatible_gap
            buffer_top_key = -dest_top
        else:
            incompatible_gap_key = -incompatible_gap
            buffer_top_key = dest_top
        support_key = -dest_top if self.prefer_taller_support_for_compatible else dest_top
        prefers_buffer_here = self.prefer_buffer_for_capped_misordered and source_capped_misordered and (cover_gap >= self.min_cover_gap_for_buffer_preference)
        if source_top_is_bad:
            if compatible:
                return (0, 0, support_key, dest_height, -dest_sorted_n, sd)
            if self.prefer_short_buffer_for_incompatible:
                return (1, 0, incompatible_gap_key, dest_height, dest_sorted_n, buffer_top_key, sd)
            return (1, 0, incompatible_gap_key, dest_sorted_n, dest_height, buffer_top_key, sd)
        if prefers_buffer_here:
            if not compatible:
                if self.prefer_short_buffer_for_incompatible:
                    return (0, 0, incompatible_gap_key, dest_height, dest_sorted_n, buffer_top_key, sd)
                return (0, 0, incompatible_gap_key, dest_sorted_n, dest_height, buffer_top_key, sd)
            sorted_key = not dest_sorted if self.prefer_sorted_when_source_good else False
            return (1, sorted_key, support_key, dest_height, -dest_sorted_n, sd)
        if compatible:
            sorted_key = not dest_sorted if self.prefer_sorted_when_source_good else False
            return (0, sorted_key, support_key, dest_height, -dest_sorted_n, sd)
        if self.prefer_short_buffer_for_incompatible:
            return (1, 0, incompatible_gap_key, dest_height, dest_sorted_n, buffer_top_key, sd)
        return (1, 0, incompatible_gap_key, dest_sorted_n, dest_height, buffer_top_key, sd)

def build_component(problem, prefer_sorted_when_source_good=True, prefer_taller_support_for_compatible=True, prefer_short_buffer_for_incompatible=True, prefer_buffer_for_capped_misordered=True, min_cover_gap_for_buffer_preference=2, prefer_smaller_incompatible_gap=True):
    return placement_machine(problem, BufferAwareBadTopPlacement(prefer_sorted_when_source_good=prefer_sorted_when_source_good, prefer_taller_support_for_compatible=prefer_taller_support_for_compatible, prefer_short_buffer_for_incompatible=prefer_short_buffer_for_incompatible, prefer_buffer_for_capped_misordered=prefer_buffer_for_capped_misordered, min_cover_gap_for_buffer_preference=min_cover_gap_for_buffer_preference, prefer_smaller_incompatible_gap=prefer_smaller_incompatible_gap))
