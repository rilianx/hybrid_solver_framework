COMPONENT = {'name': 'unsorted_to_sorted_safe_placement_v2', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'max_gap': {'type': 'int', 'range': [0, 50], 'default': 6}, 'min_source_bad': {'type': 'int', 'range': [1, 50], 'default': 1}}}
from core.rules import RuleMachine

class UnsortedToSortedSafePlacementRefined:
    """Mueve desde fuente desordenada a destino ordenado que sigue ordenado; si no hay, aparca muy controladamente en buffer."""
    name = 'unsorted_to_sorted_safe_placement'

    def __init__(self, prefer_non_empty_destination=True, prefer_equal_top=True, max_gap=6, min_source_bad=1, fallback_enable=True, fallback_max_source_height=2, fallback_min_bad_above_sorted=1, fallback_require_empty_destination=True):
        self.prefer_non_empty_destination = prefer_non_empty_destination
        self.prefer_equal_top = prefer_equal_top
        self.max_gap = max_gap
        self.min_source_bad = min_source_bad
        self.fallback_enable = fallback_enable
        self.fallback_max_source_height = fallback_max_source_height
        self.fallback_min_bad_above_sorted = fallback_min_bad_above_sorted
        self.fallback_require_empty_destination = fallback_require_empty_destination

    def _source_bad_count(self, partial, so):
        return partial.h(so) - partial.sorted_n[so]

    def _is_unsorted_source(self, partial, so):
        return partial.h(so) > 0 and (not partial.is_sorted_stack(so))

    def _keeps_destination_sorted(self, partial, so, sd):
        if so == sd or partial.h(so) == 0 or partial.h(sd) >= partial.H:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _strict_move_ok(self, partial, action):
        so, sd = (action.so, action.sd)
        if not self._is_unsorted_source(partial, so):
            return False
        if self._source_bad_count(partial, so) < self.min_source_bad:
            return False
        if not self._keeps_destination_sorted(partial, so, sd):
            return False
        gap = partial.g(sd) - partial.g(so)
        return gap <= self.max_gap

    def _fallback_move_ok(self, partial, action):
        so, sd = (action.so, action.sd)
        if not self.fallback_enable:
            return False
        if so == sd or partial.h(so) == 0 or partial.h(sd) >= partial.H:
            return False
        if not self._is_unsorted_source(partial, so):
            return False
        if partial.h(so) > self.fallback_max_source_height:
            return False
        if self._source_bad_count(partial, so) < self.fallback_min_bad_above_sorted:
            return False
        if self.fallback_require_empty_destination and partial.h(sd) != 0:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.h(sd) == 0

    def _strict_key(self, partial, action):
        so, sd = (action.so, action.sd)
        top = partial.g(so)
        dst = partial.g(sd)
        gap = dst - top
        dest_empty = partial.h(sd) == 0
        exact_fit = 0 if dst == top else 1
        source_bad = self._source_bad_count(partial, so)
        frees_sorted_source_soon = partial.sorted_n[so]
        if self.prefer_non_empty_destination:
            base = (exact_fit if self.prefer_equal_top else 0, dest_empty, gap, -source_bad, -partial.sorted_n[sd], -partial.h(sd), frees_sorted_source_soon, so, sd)
        else:
            base = (exact_fit if self.prefer_equal_top else 0, gap, dest_empty, -source_bad, -partial.sorted_n[sd], -partial.h(sd), frees_sorted_source_soon, so, sd)
        return base

    def _fallback_key(self, partial, action):
        so, sd = (action.so, action.sd)
        return (partial.h(so), -self._source_bad_count(partial, so), -partial.sorted_n[so], so, sd)

    def allowed(self, partial, memory, candidates):
        strict = [a for a in candidates if self._strict_move_ok(partial, a)]
        if strict:
            strict.sort(key=lambda a: self._strict_key(partial, a))
            return strict
        fallback = [a for a in candidates if self._fallback_move_ok(partial, a)]
        fallback.sort(key=lambda a: self._fallback_key(partial, a))
        return fallback

def build_component(problem, **params):
    rule = UnsortedToSortedSafePlacementRefined(prefer_non_empty_destination=params.get('prefer_non_empty_destination', True), prefer_equal_top=params.get('prefer_equal_top', True), max_gap=params.get('max_gap', 6), min_source_bad=params.get('min_source_bad', 1), fallback_enable=params.get('fallback_enable', True), fallback_max_source_height=params.get('fallback_max_source_height', 2), fallback_min_bad_above_sorted=params.get('fallback_min_bad_above_sorted', 1), fallback_require_empty_destination=params.get('fallback_require_empty_destination', True))
    return RuleMachine(problem, [rule])
