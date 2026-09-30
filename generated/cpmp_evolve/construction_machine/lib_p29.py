COMPONENT = {'name': 'targeted_bad_suffix_capping', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_dest_sorted_prefix': {'type': 'int', 'range': [1, 6], 'default': 2}, 'prefer_tighter_cap': {'type': 'bool', 'default': True}}}
from core.rules import RuleMachine

class TargetedBadSuffixCappingRule:
    """Permite capar una pila destino desordenada con buen prefijo ordenado usando una cima de fuente también desordenada que no supera la cima actual del destino."""
    name = 'targeted_bad_suffix_capping'

    def __init__(self, min_dest_sorted_prefix: int, max_dest_bad_suffix: int, max_source_bad_suffix: int, require_strict_cap: bool, prefer_shorter_source: bool, prefer_longer_dest_prefix: bool, prefer_tighter_cap: bool):
        self.min_dest_sorted_prefix = int(min_dest_sorted_prefix)
        self.max_dest_bad_suffix = int(max_dest_bad_suffix)
        self.max_source_bad_suffix = int(max_source_bad_suffix)
        self.require_strict_cap = bool(require_strict_cap)
        self.prefer_shorter_source = bool(prefer_shorter_source)
        self.prefer_longer_dest_prefix = bool(prefer_longer_dest_prefix)
        self.prefer_tighter_cap = bool(prefer_tighter_cap)

    def _bad_suffix_len(self, partial, s: int) -> int:
        return partial.h(s) - partial.sorted_n[s]

    def _is_unsorted_source(self, partial, s: int) -> bool:
        return partial.h(s) > 0 and (not partial.is_sorted_stack(s)) and (self._bad_suffix_len(partial, s) >= 1) and (self._bad_suffix_len(partial, s) <= self.max_source_bad_suffix)

    def _is_target_bad_suffix_dest(self, partial, s: int) -> bool:
        bad_suffix = self._bad_suffix_len(partial, s)
        return partial.e(s) > 0 and partial.h(s) > 0 and (not partial.is_sorted_stack(s)) and (partial.sorted_n[s] >= self.min_dest_sorted_prefix) and (bad_suffix >= 1) and (bad_suffix <= self.max_dest_bad_suffix)

    def _is_cap_move(self, partial, so: int, sd: int) -> bool:
        moved = partial.g(so)
        dst_top = partial.g(sd)
        if self.require_strict_cap:
            return moved < dst_top
        return moved <= dst_top

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved = partial.g(so)
        dst_top = partial.g(sd)
        gap = dst_top - moved
        src_bad = self._bad_suffix_len(partial, so)
        dst_prefix = partial.sorted_n[sd]
        src_height = partial.h(so)
        shorter_source_rank = src_height if self.prefer_shorter_source else -src_height
        longer_dest_prefix_rank = -dst_prefix if self.prefer_longer_dest_prefix else dst_prefix
        tighter_cap_rank = gap if self.prefer_tighter_cap else -gap
        return (tighter_cap_rank, longer_dest_prefix_rank, src_bad, shorter_source_rank, so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if so == sd:
                continue
            if not self._is_unsorted_source(partial, so):
                continue
            if not self._is_target_bad_suffix_dest(partial, sd):
                continue
            if not self._is_cap_move(partial, so, sd):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self._sort_key(partial, a))
        return allowed

def build_component(problem, min_dest_sorted_prefix=2, max_dest_bad_suffix=3, max_source_bad_suffix=3, require_strict_cap=True, prefer_shorter_source=True, prefer_longer_dest_prefix=True, prefer_tighter_cap=True, **params):
    rule = TargetedBadSuffixCappingRule(min_dest_sorted_prefix=min_dest_sorted_prefix, max_dest_bad_suffix=max_dest_bad_suffix, max_source_bad_suffix=max_source_bad_suffix, require_strict_cap=require_strict_cap, prefer_shorter_source=prefer_shorter_source, prefer_longer_dest_prefix=prefer_longer_dest_prefix, prefer_tighter_cap=prefer_tighter_cap)
    return RuleMachine(problem, [rule])
