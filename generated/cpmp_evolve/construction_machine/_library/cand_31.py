COMPONENT = {'name': 'unsorted_to_unsorted_bad_suffix_cap', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_dest_bad_suffix_len': {'type': 'int', 'range': [1, 6], 'default': 1}, 'min_source_bad_count': {'type': 'int', 'range': [1, 6], 'default': 1}, 'require_strict_source_relief': {'type': 'bool', 'default': False}, 'prefer_longer_dest_bad_suffix': {'type': 'bool', 'default': True}, 'prefer_tighter_fit': {'type': 'bool', 'default': True}}}
from core.rules import RuleMachine

class UnsortedToUnsortedBadSuffixCap:
    """Permite mover desde una fuente desordenada a un destino desordenado cuando la pieza encaja sobre la tapa mala ya ordenada del destino."""
    name = 'unsorted_to_unsorted_bad_suffix_cap'

    def __init__(self, min_dest_bad_suffix_len: int, min_source_bad_count: int, require_strict_source_relief: bool, prefer_longer_dest_bad_suffix: bool, prefer_tighter_fit: bool, prefer_more_filled_dest: bool):
        self.min_dest_bad_suffix_len = int(min_dest_bad_suffix_len)
        self.min_source_bad_count = int(min_source_bad_count)
        self.require_strict_source_relief = bool(require_strict_source_relief)
        self.prefer_longer_dest_bad_suffix = bool(prefer_longer_dest_bad_suffix)
        self.prefer_tighter_fit = bool(prefer_tighter_fit)
        self.prefer_more_filled_dest = bool(prefer_more_filled_dest)

    def _bad_count(self, partial, s: int) -> int:
        return partial.h(s) - partial.sorted_n[s]

    def _dest_bad_suffix_len(self, partial, s: int) -> int:
        return self._bad_count(partial, s)

    def _source_ok(self, partial, s: int) -> bool:
        return partial.h(s) > 0 and (not partial.is_sorted_stack(s)) and (self._bad_count(partial, s) >= self.min_source_bad_count)

    def _dest_ok(self, partial, s: int) -> bool:
        return partial.e(s) > 0 and (not partial.is_sorted_stack(s)) and (self._dest_bad_suffix_len(partial, s) >= self.min_dest_bad_suffix_len)

    def _caps_dest_suffix(self, partial, so: int, sd: int) -> bool:
        moved = partial.g(so)
        dest_top = partial.g(sd)
        return moved <= dest_top

    def _source_relief_ok(self, partial, so: int) -> bool:
        if not self.require_strict_source_relief:
            return True
        return partial.h(so) >= 2 and partial.g(so) < partial.g(so)

    def _strict_source_relief(self, partial, so: int) -> bool:
        if partial.h(so) < 2:
            return False
        top = partial.stacks[so][-1]
        below = partial.stacks[so][-2]
        return below < top

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if so == sd:
                continue
            if not self._source_ok(partial, so):
                continue
            if not self._dest_ok(partial, sd):
                continue
            if not self._caps_dest_suffix(partial, so, sd):
                continue
            if self.require_strict_source_relief and (not self._strict_source_relief(partial, so)):
                continue
            allowed.append(action)

        def key(action):
            so = action.so
            sd = action.sd
            moved = partial.g(so)
            dest_top = partial.g(sd)
            dest_suffix = self._dest_bad_suffix_len(partial, sd)
            src_bad = self._bad_count(partial, so)
            fit_gap = dest_top - moved
            return (-dest_suffix if self.prefer_longer_dest_bad_suffix else dest_suffix, fit_gap if self.prefer_tighter_fit else -fit_gap, -partial.h(sd) if self.prefer_more_filled_dest else partial.h(sd), -src_bad, so, sd)
        allowed.sort(key=key)
        return allowed

def build_component(problem, min_dest_bad_suffix_len=1, min_source_bad_count=1, require_strict_source_relief=False, prefer_longer_dest_bad_suffix=True, prefer_tighter_fit=True, prefer_more_filled_dest=True):
    rule = UnsortedToUnsortedBadSuffixCap(min_dest_bad_suffix_len=min_dest_bad_suffix_len, min_source_bad_count=min_source_bad_count, require_strict_source_relief=require_strict_source_relief, prefer_longer_dest_bad_suffix=prefer_longer_dest_bad_suffix, prefer_tighter_fit=prefer_tighter_fit, prefer_more_filled_dest=prefer_more_filled_dest)
    return RuleMachine(problem, [rule])
