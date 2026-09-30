from core.rules import RuleMachine
COMPONENT = {'name': 'single_blocker_to_sorted_safe_placement', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_sorted_prefix': {'type': 'int', 'range': [1, 10], 'default': 1}, 'max_source_height': {'type': 'int', 'range': [1, 10], 'default': 10}, 'prefer_tighter_group_fit': {'type': 'bool', 'default': True}}}

class SingleBlockerToSortedSafePlacement:
    """Permite mover el único bloqueador del tope de una pila casi ordenada a una pila destino ordenada sin desordenarla."""
    name = 'single_blocker_to_sorted_safe_placement'

    def __init__(self, min_sorted_prefix: int, max_source_height: int, prefer_non_empty_destination: bool, prefer_tighter_group_fit: bool, prefer_shorter_source: bool):
        self.min_sorted_prefix = int(min_sorted_prefix)
        self.max_source_height = int(max_source_height)
        self.prefer_non_empty_destination = bool(prefer_non_empty_destination)
        self.prefer_tighter_group_fit = bool(prefer_tighter_group_fit)
        self.prefer_shorter_source = bool(prefer_shorter_source)

    def _bad_count(self, partial, stack: int) -> int:
        return partial.h(stack) - partial.sorted_n[stack]

    def _is_single_blocker_source(self, partial, stack: int) -> bool:
        height = partial.h(stack)
        return height >= 2 and height <= self.max_source_height and (not partial.is_sorted_stack(stack)) and (partial.sorted_n[stack] >= self.min_sorted_prefix) and (self._bad_count(partial, stack) == 1)

    def _keeps_destination_sorted(self, partial, so: int, sd: int) -> bool:
        return partial.e(sd) > 0 and partial.is_sorted_stack(sd) and (partial.g(sd) >= partial.g(so))

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved_group = partial.g(so)
        dst_top = partial.g(sd)
        dst_empty = partial.h(sd) == 0
        src_height = partial.h(so)
        gap = dst_top - moved_group
        exposed_sorted_after_move = partial.sorted_n[so] == partial.h(so) - 1
        non_empty_rank = dst_empty if self.prefer_non_empty_destination else not dst_empty
        fit_rank = gap if self.prefer_tighter_group_fit else -gap
        source_rank = src_height if self.prefer_shorter_source else -src_height
        return (non_empty_rank, not exposed_sorted_after_move, fit_rank, source_rank, -partial.sorted_n[sd], -partial.h(sd), so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            if not self._is_single_blocker_source(partial, action.so):
                continue
            if not self._keeps_destination_sorted(partial, action.so, action.sd):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self._sort_key(partial, a))
        return allowed

def build_component(problem, min_sorted_prefix=1, max_source_height=10, prefer_non_empty_destination=True, prefer_tighter_group_fit=True, prefer_shorter_source=True, **params):
    rule = SingleBlockerToSortedSafePlacement(min_sorted_prefix=min_sorted_prefix, max_source_height=max_source_height, prefer_non_empty_destination=prefer_non_empty_destination, prefer_tighter_group_fit=prefer_tighter_group_fit, prefer_shorter_source=prefer_shorter_source)
    return RuleMachine(problem, [rule])
