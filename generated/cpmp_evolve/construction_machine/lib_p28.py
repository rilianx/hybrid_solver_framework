from core.rules import RuleMachine
COMPONENT = {'name': 'capped_bad_suffix_transfer', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_dest_sorted_prefix': {'type': 'int', 'range': [1, 10], 'default': 2}, 'min_dest_bad_suffix': {'type': 'int', 'range': [1, 10], 'default': 1}, 'min_source_bad_suffix': {'type': 'int', 'range': [1, 10], 'default': 1}, 'prefer_tighter_cap_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.0}}}

class CappedBadSuffixTransfer:
    """Permite capar un receptor desordenado con buen prefijo ordenado moviendo desde una fuente desordenada."""
    name = 'capped_bad_suffix_transfer'

    def __init__(self, min_dest_sorted_prefix: int, min_dest_bad_suffix: int, max_dest_bad_suffix: int, min_source_bad_suffix: int, max_source_bad_suffix: int, prefer_tighter_cap_weight: float, prefer_shorter_dest_bad_suffix_weight: float, prefer_longer_dest_prefix_weight: float, prefer_smaller_source_bad_suffix_weight: float, prefer_shorter_source_height_weight: float):
        self.min_dest_sorted_prefix = int(min_dest_sorted_prefix)
        self.min_dest_bad_suffix = int(min_dest_bad_suffix)
        self.max_dest_bad_suffix = int(max_dest_bad_suffix)
        self.min_source_bad_suffix = int(min_source_bad_suffix)
        self.max_source_bad_suffix = int(max_source_bad_suffix)
        self.prefer_tighter_cap_weight = float(prefer_tighter_cap_weight)
        self.prefer_shorter_dest_bad_suffix_weight = float(prefer_shorter_dest_bad_suffix_weight)
        self.prefer_longer_dest_prefix_weight = float(prefer_longer_dest_prefix_weight)
        self.prefer_smaller_source_bad_suffix_weight = float(prefer_smaller_source_bad_suffix_weight)
        self.prefer_shorter_source_height_weight = float(prefer_shorter_source_height_weight)

    def _bad_count(self, partial, s: int) -> int:
        return partial.h(s) - partial.sorted_n[s]

    def _is_unsorted_source(self, partial, s: int) -> bool:
        if partial.h(s) == 0:
            return False
        if partial.is_sorted_stack(s):
            return False
        bad = self._bad_count(partial, s)
        return self.min_source_bad_suffix <= bad <= self.max_source_bad_suffix

    def _is_target_bad_suffix_dest(self, partial, s: int) -> bool:
        if partial.h(s) == 0 or partial.e(s) == 0:
            return False
        if partial.is_sorted_stack(s):
            return False
        bad = self._bad_count(partial, s)
        return partial.sorted_n[s] >= self.min_dest_sorted_prefix and self.min_dest_bad_suffix <= bad <= self.max_dest_bad_suffix

    def _is_capping_move(self, partial, so: int, sd: int) -> bool:
        return partial.g(sd) >= partial.g(so)

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
            if not self._is_capping_move(partial, so, sd):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self.score(partial, memory, a))
        return allowed

    def score(self, partial, memory, action):
        so = action.so
        sd = action.sd
        moved = partial.g(so)
        dest_top = partial.g(sd)
        cap_gap = dest_top - moved
        dest_bad = self._bad_count(partial, sd)
        dest_prefix = partial.sorted_n[sd]
        src_bad = self._bad_count(partial, so)
        src_h = partial.h(so)
        return self.prefer_tighter_cap_weight * float(cap_gap) + self.prefer_shorter_dest_bad_suffix_weight * float(dest_bad) - self.prefer_longer_dest_prefix_weight * float(dest_prefix) + self.prefer_smaller_source_bad_suffix_weight * float(src_bad) + self.prefer_shorter_source_height_weight * float(src_h)

def build_component(problem, min_dest_sorted_prefix=2, min_dest_bad_suffix=1, max_dest_bad_suffix=2, min_source_bad_suffix=1, max_source_bad_suffix=4, prefer_tighter_cap_weight=1.0, prefer_shorter_dest_bad_suffix_weight=2.0, prefer_longer_dest_prefix_weight=1.0, prefer_smaller_source_bad_suffix_weight=0.5, prefer_shorter_source_height_weight=0.25):
    rule = CappedBadSuffixTransfer(min_dest_sorted_prefix=min_dest_sorted_prefix, min_dest_bad_suffix=min_dest_bad_suffix, max_dest_bad_suffix=max_dest_bad_suffix, min_source_bad_suffix=min_source_bad_suffix, max_source_bad_suffix=max_source_bad_suffix, prefer_tighter_cap_weight=prefer_tighter_cap_weight, prefer_shorter_dest_bad_suffix_weight=prefer_shorter_dest_bad_suffix_weight, prefer_longer_dest_prefix_weight=prefer_longer_dest_prefix_weight, prefer_smaller_source_bad_suffix_weight=prefer_smaller_source_bad_suffix_weight, prefer_shorter_source_height_weight=prefer_shorter_source_height_weight)
    return RuleMachine(problem, [rule])
