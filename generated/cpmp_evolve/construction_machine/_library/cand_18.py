from core.rules import RuleMachine
COMPONENT = {'name': 'single_blocker_to_empty_buffer', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_sorted_prefix': {'type': 'int', 'range': [1, 10], 'default': 1}, 'max_source_height': {'type': 'int', 'range': [1, 10], 'default': 10}}}

class SingleBlockerToEmptyBufferRule:
    """Permite mover a un buffer vacío el único bloqueador superior de una pila casi ordenada."""
    name = 'single_blocker_to_empty_buffer'

    def __init__(self, min_sorted_prefix: int, max_source_height: int, prefer_shorter_source: bool, prefer_tighter_group: bool):
        self.min_sorted_prefix = int(min_sorted_prefix)
        self.max_source_height = int(max_source_height)
        self.prefer_shorter_source = bool(prefer_shorter_source)
        self.prefer_tighter_group = bool(prefer_tighter_group)

    def _bad_count(self, partial, stack: int) -> int:
        return partial.h(stack) - partial.sorted_n[stack]

    def _is_single_blocker_source(self, partial, stack: int) -> bool:
        height = partial.h(stack)
        return height >= 2 and height <= self.max_source_height and (self._bad_count(partial, stack) == 1) and (partial.sorted_n[stack] >= self.min_sorted_prefix)

    def _is_empty_buffer(self, partial, stack: int) -> bool:
        return partial.h(stack) == 0 and partial.e(stack) > 0

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        source_height = partial.h(so)
        moved_group = partial.g(so)
        exposed_group = partial.stacks[so][-2] if source_height >= 2 else partial.G
        gap = moved_group - exposed_group
        source_rank = source_height if self.prefer_shorter_source else -source_height
        gap_rank = abs(gap) if self.prefer_tighter_group else -abs(gap)
        return (source_rank, gap_rank, -partial.sorted_n[so], so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            if not self._is_single_blocker_source(partial, action.so):
                continue
            if not self._is_empty_buffer(partial, action.sd):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self._sort_key(partial, a))
        return allowed

def build_component(problem, min_sorted_prefix=1, max_source_height=10, prefer_shorter_source=True, prefer_tighter_group=True, **params):
    rule = SingleBlockerToEmptyBufferRule(min_sorted_prefix=min_sorted_prefix, max_source_height=max_source_height, prefer_shorter_source=prefer_shorter_source, prefer_tighter_group=prefer_tighter_group)
    return RuleMachine(problem, [rule])
