COMPONENT = {'name': 'unsorted_to_sorted_safe_placement_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'enable_capped_parking_fallback': {'type': 'bool', 'default': True}, 'max_bad_suffix': {'type': 'int', 'range': [1, 4], 'default': 1}, 'min_sorted_prefix': {'type': 'int', 'range': [0, 10], 'default': 1}}}
from core.rules import RuleMachine

class UnsortedToSortedSafePlacement:
    """Mueve desde una fuente desordenada a un destino ordenado que sigue ordenado; como respaldo, permite un aparcamiento tapado muy controlado."""
    name = 'unsorted_to_sorted_safe_placement'

    def __init__(self, prefer_non_empty_destination: bool=True, gap_tolerance: int=1, enable_capped_parking_fallback: bool=True, max_bad_suffix: int=1, min_sorted_prefix: int=1):
        self.prefer_non_empty_destination = prefer_non_empty_destination
        self.gap_tolerance = gap_tolerance
        self.enable_capped_parking_fallback = enable_capped_parking_fallback
        self.max_bad_suffix = max_bad_suffix
        self.min_sorted_prefix = min_sorted_prefix

    def _is_unsorted_source(self, partial, so):
        return partial.h(so) > 0 and (not partial.is_sorted_stack(so))

    def _keeps_destination_sorted(self, partial, so, sd):
        if partial.h(so) == 0 or partial.h(sd) >= partial.H:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _source_becomes_sorted_after_move(self, partial, so):
        return partial.h(so) > 0 and partial.sorted_n[so] >= partial.h(so) - 1

    def _bad_suffix_len(self, partial, sd):
        return partial.h(sd) - partial.sorted_n[sd]

    def _is_capped_parking_destination(self, partial, so, sd):
        if partial.h(so) == 0 or partial.h(sd) >= partial.H:
            return False
        if partial.is_sorted_stack(sd):
            return False
        if partial.sorted_n[sd] < self.min_sorted_prefix:
            return False
        bad_suffix = self._bad_suffix_len(partial, sd)
        if bad_suffix < 1 or bad_suffix > self.max_bad_suffix:
            return False
        return partial.g(sd) >= partial.g(so)

    def allowed(self, partial, memory, candidates):
        safe_by_source = {}
        fallback = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if not self._is_unsorted_source(partial, so):
                continue
            if self._keeps_destination_sorted(partial, so, sd):
                safe_by_source.setdefault(so, []).append(action)
            elif self.enable_capped_parking_fallback and self._source_becomes_sorted_after_move(partial, so) and self._is_capped_parking_destination(partial, so, sd):
                fallback.append(action)
        allowed = []
        for so, actions in safe_by_source.items():
            best_gap = min((partial.g(a.sd) - partial.g(a.so) for a in actions))
            for action in actions:
                gap = partial.g(action.sd) - partial.g(action.so)
                if gap <= best_gap + self.gap_tolerance or self._source_becomes_sorted_after_move(partial, so):
                    allowed.append(action)
        if not allowed:
            allowed = fallback
        else:
            allowed.extend(fallback)

        def key(action):
            so = action.so
            sd = action.sd
            dest_sorted = partial.is_sorted_stack(sd)
            source_sorts = self._source_becomes_sorted_after_move(partial, so)
            gap = partial.g(sd) - partial.g(so)
            dest_empty = partial.h(sd) == 0
            bad_suffix = self._bad_suffix_len(partial, sd)
            if self.prefer_non_empty_destination:
                return (not source_sorts, not dest_sorted, dest_empty, gap, bad_suffix, -partial.sorted_n[sd], -partial.h(sd), so, sd)
            return (not source_sorts, not dest_sorted, gap, dest_empty, bad_suffix, -partial.sorted_n[sd], -partial.h(sd), so, sd)
        allowed.sort(key=key)
        return allowed

def build_component(problem, **params):
    rule = UnsortedToSortedSafePlacement(prefer_non_empty_destination=params.get('prefer_non_empty_destination', True), gap_tolerance=params.get('gap_tolerance', 1), enable_capped_parking_fallback=params.get('enable_capped_parking_fallback', True), max_bad_suffix=params.get('max_bad_suffix', 1), min_sorted_prefix=params.get('min_sorted_prefix', 1))
    return RuleMachine(problem, [rule])
