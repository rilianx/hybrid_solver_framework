from core.rules import RuleMachine
COMPONENT = {'name': 'multi_blocker_peel_to_empty_buffer', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_bad_suffix': {'type': 'int', 'range': [2, 6], 'default': 2}, 'min_sorted_prefix': {'type': 'int', 'range': [0, 10], 'default': 1}, 'min_source_height': {'type': 'int', 'range': [1, 10], 'default': 3}}}

class MultiBlockerPeelToEmptyBuffer:
    """Permite pelar la cima de una fuente desordenada con varios bloqueadores hacia un buffer vacío."""
    name = 'multi_blocker_peel_to_empty_buffer'

    def __init__(self, min_bad_suffix: int, max_bad_suffix: int, min_sorted_prefix: int, min_source_height: int, prefer_taller_sources: bool, prefer_smaller_bad_suffix: bool, prefer_larger_sorted_prefix: bool):
        self.min_bad_suffix = int(min_bad_suffix)
        self.max_bad_suffix = int(max_bad_suffix)
        self.min_sorted_prefix = int(min_sorted_prefix)
        self.min_source_height = int(min_source_height)
        self.prefer_taller_sources = bool(prefer_taller_sources)
        self.prefer_smaller_bad_suffix = bool(prefer_smaller_bad_suffix)
        self.prefer_larger_sorted_prefix = bool(prefer_larger_sorted_prefix)

    def _bad_suffix(self, partial, stack: int) -> int:
        return partial.h(stack) - partial.sorted_n[stack]

    def _eligible_source(self, partial, stack: int) -> bool:
        if partial.h(stack) < self.min_source_height:
            return False
        if partial.is_sorted_stack(stack):
            return False
        if partial.sorted_n[stack] < self.min_sorted_prefix:
            return False
        bad_suffix = self._bad_suffix(partial, stack)
        return self.min_bad_suffix <= bad_suffix <= self.max_bad_suffix

    def _eligible_dest(self, partial, stack: int) -> bool:
        return partial.h(stack) == 0 and partial.e(stack) > 0

    def _sort_key(self, partial, action):
        so = action.so
        bad_suffix = self._bad_suffix(partial, so)
        source_height = partial.h(so)
        sorted_prefix = partial.sorted_n[so]
        height_rank = -source_height if self.prefer_taller_sources else source_height
        bad_rank = bad_suffix if self.prefer_smaller_bad_suffix else -bad_suffix
        prefix_rank = -sorted_prefix if self.prefer_larger_sorted_prefix else sorted_prefix
        return (bad_rank, prefix_rank, height_rank, partial.g(so), so, action.sd)

    def allowed(self, partial, memory, candidates):
        allowed = [action for action in candidates if self._eligible_source(partial, action.so) and self._eligible_dest(partial, action.sd)]
        allowed.sort(key=lambda action: self._sort_key(partial, action))
        return allowed

def build_component(problem, min_bad_suffix=2, max_bad_suffix=4, min_sorted_prefix=1, min_source_height=3, prefer_taller_sources=True, prefer_smaller_bad_suffix=True, prefer_larger_sorted_prefix=True, **params):
    rule = MultiBlockerPeelToEmptyBuffer(min_bad_suffix=min_bad_suffix, max_bad_suffix=max_bad_suffix, min_sorted_prefix=min_sorted_prefix, min_source_height=min_source_height, prefer_taller_sources=prefer_taller_sources, prefer_smaller_bad_suffix=prefer_smaller_bad_suffix, prefer_larger_sorted_prefix=prefer_larger_sorted_prefix)
    return RuleMachine(problem, [rule])
