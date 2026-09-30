COMPONENT = {'name': 'unsorted_to_sorted_safe_placement_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from core.rules import RuleMachine

class UnsortedToSortedSafePlacementRefined:
    """Move from an unsorted source stack to a sorted destination stack while keeping the destination sorted."""
    name = 'unsorted_to_sorted_safe_placement'

    def __init__(self, prefer_non_empty_destination: bool=True, prefer_exact_fit: bool=True, prefer_short_bad_suffix: bool=True, prefer_taller_sorted_destination: bool=True):
        self.prefer_non_empty_destination = prefer_non_empty_destination
        self.prefer_exact_fit = prefer_exact_fit
        self.prefer_short_bad_suffix = prefer_short_bad_suffix
        self.prefer_taller_sorted_destination = prefer_taller_sorted_destination

    def _is_unsorted_source(self, partial, so):
        return partial.h(so) > 0 and (not partial.is_sorted_stack(so))

    def _keeps_destination_sorted(self, partial, so, sd):
        if so == sd or partial.h(so) == 0 or partial.h(sd) >= partial.H:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _bad_suffix_len(self, partial, s):
        return partial.h(s) - partial.sorted_n[s]

    def _key(self, partial, action):
        top_group = partial.g(action.so)
        dest_top = partial.g(action.sd)
        gap = dest_top - top_group
        dest_empty = partial.h(action.sd) == 0
        exact_fit = not dest_empty and gap == 0
        bad_suffix = self._bad_suffix_len(partial, action.so)
        key = []
        if self.prefer_exact_fit:
            key.append(not exact_fit)
        if self.prefer_non_empty_destination:
            key.append(dest_empty)
        key.append(gap)
        if self.prefer_short_bad_suffix:
            key.append(bad_suffix)
        if self.prefer_taller_sorted_destination:
            key.append(-partial.sorted_n[action.sd])
            key.append(-partial.h(action.sd))
        key.append(-partial.sorted_n[action.so])
        key.append(action.so)
        key.append(action.sd)
        return tuple(key)

    def allowed(self, partial, memory, candidates):
        allowed = [action for action in candidates if self._is_unsorted_source(partial, action.so) and self._keeps_destination_sorted(partial, action.so, action.sd)]
        allowed.sort(key=lambda action: self._key(partial, action))
        return allowed

def build_component(problem, **params):
    rule = UnsortedToSortedSafePlacementRefined(prefer_non_empty_destination=params.get('prefer_non_empty_destination', True), prefer_exact_fit=params.get('prefer_exact_fit', True), prefer_short_bad_suffix=params.get('prefer_short_bad_suffix', True), prefer_taller_sorted_destination=params.get('prefer_taller_sorted_destination', True))
    return RuleMachine(problem, [rule])
