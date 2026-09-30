COMPONENT = {'name': 'unsorted_to_unsorted_top_capping', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_sorted_prefix': {'type': 'int', 'range': [0, 6], 'default': 1}, 'min_dest_sorted_prefix': {'type': 'int', 'range': [0, 6], 'default': 1}, 'max_source_bad_suffix': {'type': 'int', 'range': [1, 6], 'default': 3}, 'max_dest_bad_suffix': {'type': 'int', 'range': [1, 6], 'default': 3}, 'prefer_tighter_cap_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.0}, 'prefer_shorter_bad_suffix_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.5}}}
from core.rules import RuleMachine

class UnsortedToUnsortedTopCappingRule:
    """Permite mover desde una fuente desordenada a un destino desordenado cuando el movido no supera el tope malo del destino."""
    name = 'unsorted_to_unsorted_top_capping'

    def __init__(self, min_source_sorted_prefix: int, min_dest_sorted_prefix: int, max_source_bad_suffix: int, max_dest_bad_suffix: int, require_strict_cap: bool, prefer_tighter_cap_weight: float, prefer_shorter_bad_suffix_weight: float, prefer_more_filled_dest_weight: float):
        self.min_source_sorted_prefix = int(min_source_sorted_prefix)
        self.min_dest_sorted_prefix = int(min_dest_sorted_prefix)
        self.max_source_bad_suffix = int(max_source_bad_suffix)
        self.max_dest_bad_suffix = int(max_dest_bad_suffix)
        self.require_strict_cap = bool(require_strict_cap)
        self.prefer_tighter_cap_weight = float(prefer_tighter_cap_weight)
        self.prefer_shorter_bad_suffix_weight = float(prefer_shorter_bad_suffix_weight)
        self.prefer_more_filled_dest_weight = float(prefer_more_filled_dest_weight)

    def _bad_suffix_len(self, partial, s: int) -> int:
        return partial.h(s) - partial.sorted_n[s]

    def _is_eligible_unsorted_source(self, partial, s: int) -> bool:
        if partial.h(s) == 0 or partial.is_sorted_stack(s):
            return False
        if partial.sorted_n[s] < self.min_source_sorted_prefix:
            return False
        bad_suffix = self._bad_suffix_len(partial, s)
        return 1 <= bad_suffix <= self.max_source_bad_suffix

    def _is_eligible_unsorted_dest(self, partial, s: int) -> bool:
        if partial.e(s) == 0 or partial.h(s) == 0 or partial.is_sorted_stack(s):
            return False
        if partial.sorted_n[s] < self.min_dest_sorted_prefix:
            return False
        bad_suffix = self._bad_suffix_len(partial, s)
        return 1 <= bad_suffix <= self.max_dest_bad_suffix

    def _caps_destination_top(self, partial, so: int, sd: int) -> bool:
        moved = partial.g(so)
        dst_top = partial.g(sd)
        if self.require_strict_cap:
            return dst_top > moved
        return dst_top >= moved

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if so == sd:
                continue
            if not self._is_eligible_unsorted_source(partial, so):
                continue
            if not self._is_eligible_unsorted_dest(partial, sd):
                continue
            if not self._caps_destination_top(partial, so, sd):
                continue
            allowed.append(action)
        return sorted(allowed, key=lambda a: self.score(partial, memory, a))

    def score(self, partial, memory, action):
        so = action.so
        sd = action.sd
        moved = partial.g(so)
        dst_top = partial.g(sd)
        cap_gap = dst_top - moved
        src_bad = self._bad_suffix_len(partial, so)
        dst_bad = self._bad_suffix_len(partial, sd)
        dst_height = partial.h(sd)
        return self.prefer_tighter_cap_weight * float(cap_gap) + self.prefer_shorter_bad_suffix_weight * float(src_bad + dst_bad) - self.prefer_more_filled_dest_weight * float(dst_height)

def build_component(problem, min_source_sorted_prefix=1, min_dest_sorted_prefix=1, max_source_bad_suffix=3, max_dest_bad_suffix=3, require_strict_cap=False, prefer_tighter_cap_weight=1.0, prefer_shorter_bad_suffix_weight=0.5, prefer_more_filled_dest_weight=0.2, **params):
    rule = UnsortedToUnsortedTopCappingRule(min_source_sorted_prefix=min_source_sorted_prefix, min_dest_sorted_prefix=min_dest_sorted_prefix, max_source_bad_suffix=max_source_bad_suffix, max_dest_bad_suffix=max_dest_bad_suffix, require_strict_cap=require_strict_cap, prefer_tighter_cap_weight=prefer_tighter_cap_weight, prefer_shorter_bad_suffix_weight=prefer_shorter_bad_suffix_weight, prefer_more_filled_dest_weight=prefer_more_filled_dest_weight)
    return RuleMachine(problem, [rule])
