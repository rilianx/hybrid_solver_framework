COMPONENT = {'name': 'unsorted_to_sorted_safe_placement_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_bad': {'type': 'int', 'range': [1, 64], 'default': 1}, 'max_gap': {'type': 'int', 'range': [0, 64], 'default': 64}}}
from core.rules import RuleMachine

class UnsortedToSortedSafePlacement:
    """Mueve desde una fuente desordenada a un destino ordenado manteniéndolo ordenado, priorizando encajes ajustados y pelados útiles."""
    name = 'unsorted_to_sorted_safe_placement'

    def __init__(self, prefer_non_empty_destination: bool=True, prefer_exact_fit: bool=True, single_blocker_first: bool=True, min_source_bad: int=1, max_gap: int=64):
        self.prefer_non_empty_destination = prefer_non_empty_destination
        self.prefer_exact_fit = prefer_exact_fit
        self.single_blocker_first = single_blocker_first
        self.min_source_bad = min_source_bad
        self.max_gap = max_gap

    def _source_bad_count(self, partial, so):
        return partial.h(so) - partial.sorted_n[so]

    def _is_unsorted_source(self, partial, so):
        if partial.h(so) == 0:
            return False
        if partial.is_sorted_stack(so):
            return False
        return self._source_bad_count(partial, so) >= self.min_source_bad

    def _keeps_destination_sorted(self, partial, so, sd):
        if so == sd:
            return False
        if partial.h(so) == 0 or partial.h(sd) >= partial.H:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        gap = partial.g(sd) - partial.g(so)
        return 0 <= gap <= self.max_gap

    def _is_single_blocker_source(self, partial, so):
        return partial.h(so) > 0 and partial.sorted_n[so] == partial.h(so) - 1

    def allowed(self, partial, memory, candidates):
        allowed = [action for action in candidates if self._is_unsorted_source(partial, action.so) and self._keeps_destination_sorted(partial, action.so, action.sd)]

        def key(action):
            so, sd = (action.so, action.sd)
            gap = partial.g(sd) - partial.g(so)
            dest_empty = partial.h(sd) == 0
            exact_fit = 0 if gap == 0 else 1
            single_blocker = 0 if self._is_single_blocker_source(partial, so) else 1
            src_bad = self._source_bad_count(partial, so)
            parts = []
            if self.single_blocker_first:
                parts.append(single_blocker)
            if self.prefer_exact_fit:
                parts.append(exact_fit)
            if self.prefer_non_empty_destination:
                parts.append(dest_empty)
            parts.extend([gap, -src_bad, -partial.sorted_n[sd], -partial.h(sd), so, sd])
            return tuple(parts)
        allowed.sort(key=key)
        return allowed

def build_component(problem, **params):
    rule = UnsortedToSortedSafePlacement(prefer_non_empty_destination=params.get('prefer_non_empty_destination', True), prefer_exact_fit=params.get('prefer_exact_fit', True), single_blocker_first=params.get('single_blocker_first', True), min_source_bad=params.get('min_source_bad', 1), max_gap=params.get('max_gap', 64))
    return RuleMachine(problem, [rule])
