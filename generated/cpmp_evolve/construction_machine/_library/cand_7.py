COMPONENT = {'name': 'buffer_aware_bad_top_placement', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'prefer_sorted_when_source_good': {'type': 'bool', 'default': True}, 'prefer_taller_support_for_compatible': {'type': 'bool', 'default': True}}}
from core.parts import placement_machine

class BufferAwareBadTopPlacement:
    """Ordena destinos separando colocación compatible de aparcado en buffer con menor gap."""
    name = 'buffer_aware_bad_top_placement'

    def __init__(self, prefer_sorted_when_source_good: bool, prefer_taller_support_for_compatible: bool, prefer_short_buffer_for_incompatible: bool, prefer_taller_support_for_incompatible: bool, prefer_more_sorted_for_incompatible: bool):
        self.prefer_sorted_when_source_good = bool(prefer_sorted_when_source_good)
        self.prefer_taller_support_for_compatible = bool(prefer_taller_support_for_compatible)
        self.prefer_short_buffer_for_incompatible = bool(prefer_short_buffer_for_incompatible)
        self.prefer_taller_support_for_incompatible = bool(prefer_taller_support_for_incompatible)
        self.prefer_more_sorted_for_incompatible = bool(prefer_more_sorted_for_incompatible)

    def rank(self, partial, action):
        so = action.so
        sd = action.sd
        source_stack = partial.stacks[so]
        moved = source_stack[-1]
        source_height = partial.h(so)
        below = source_stack[-2] if source_height >= 2 else partial.G
        source_top_is_bad = source_height >= 2 and moved > below
        dest_top = partial.g(sd)
        dest_height = partial.h(sd)
        dest_sorted = partial.is_sorted_stack(sd)
        dest_sorted_n = partial.sorted_n[sd]
        compatible = moved <= dest_top
        if compatible:
            support_key = -dest_top if self.prefer_taller_support_for_compatible else dest_top
            if source_top_is_bad:
                return (False, False, support_key, dest_height, -dest_sorted_n, sd)
            sorted_key = not dest_sorted if self.prefer_sorted_when_source_good else False
            return (False, sorted_key, support_key, dest_height, -dest_sorted_n, sd)
        incompatible_support_key = -dest_top if self.prefer_taller_support_for_incompatible else dest_top
        incompatible_sorted_key = -dest_sorted_n if self.prefer_more_sorted_for_incompatible else dest_sorted_n
        incompatible_height_key = dest_height if self.prefer_short_buffer_for_incompatible else -dest_height
        return (True, incompatible_support_key, incompatible_height_key, incompatible_sorted_key, sd)

def build_component(problem, prefer_sorted_when_source_good=True, prefer_taller_support_for_compatible=True, prefer_short_buffer_for_incompatible=True, prefer_taller_support_for_incompatible=True, prefer_more_sorted_for_incompatible=True):
    return placement_machine(problem, BufferAwareBadTopPlacement(prefer_sorted_when_source_good=prefer_sorted_when_source_good, prefer_taller_support_for_compatible=prefer_taller_support_for_compatible, prefer_short_buffer_for_incompatible=prefer_short_buffer_for_incompatible, prefer_taller_support_for_incompatible=prefer_taller_support_for_incompatible, prefer_more_sorted_for_incompatible=prefer_more_sorted_for_incompatible))
