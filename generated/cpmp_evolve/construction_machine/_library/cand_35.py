from core.rules import RuleMachine
COMPONENT = {'name': 'frontier_blocker_to_unsorted_parking', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'single_bad_count': {'type': 'int', 'range': [1, 3], 'default': 1}, 'frontier_max_height': {'type': 'int', 'range': [1, 6], 'default': 2}, 'min_source_sorted_prefix': {'type': 'int', 'range': [0, 6], 'default': 1}, 'min_dest_bad_suffix': {'type': 'int', 'range': [1, 6], 'default': 1}, 'min_dest_sorted_prefix': {'type': 'int', 'range': [0, 6], 'default': 0}, 'prefer_single_blocker_source': {'type': 'bool', 'default': True}, 'prefer_taller_destination': {'type': 'bool', 'default': True}, 'prefer_smaller_dest_top': {'type': 'bool', 'default': True}}}

class FrontierBlockerToUnsortedParking:
    """Permite aparcar bloqueadores de frontera en una pila destino desordenada y no vacía."""
    name = 'frontier_blocker_to_unsorted_parking'

    def __init__(self, single_bad_count: int, frontier_max_height: int, min_source_sorted_prefix: int, min_dest_bad_suffix: int, min_dest_sorted_prefix: int, require_strict_parking: bool, prefer_single_blocker_source: bool, prefer_shorter_source: bool, prefer_taller_destination: bool, prefer_smaller_dest_top: bool):
        self.single_bad_count = int(single_bad_count)
        self.frontier_max_height = int(frontier_max_height)
        self.min_source_sorted_prefix = int(min_source_sorted_prefix)
        self.min_dest_bad_suffix = int(min_dest_bad_suffix)
        self.min_dest_sorted_prefix = int(min_dest_sorted_prefix)
        self.require_strict_parking = bool(require_strict_parking)
        self.prefer_single_blocker_source = bool(prefer_single_blocker_source)
        self.prefer_shorter_source = bool(prefer_shorter_source)
        self.prefer_taller_destination = bool(prefer_taller_destination)
        self.prefer_smaller_dest_top = bool(prefer_smaller_dest_top)

    def _bad_count(self, partial, stack: int) -> int:
        return partial.h(stack) - partial.sorted_n[stack]

    def _is_sorted_frontier_source(self, partial, stack: int) -> bool:
        return partial.h(stack) > 0 and partial.h(stack) <= self.frontier_max_height and partial.is_sorted_stack(stack) and (partial.sorted_n[stack] >= self.min_source_sorted_prefix)

    def _is_single_blocker_source(self, partial, stack: int) -> bool:
        return partial.h(stack) > self.single_bad_count and self._bad_count(partial, stack) == self.single_bad_count and (partial.sorted_n[stack] >= self.min_source_sorted_prefix)

    def _source_kind(self, partial, stack: int):
        if self._is_single_blocker_source(partial, stack):
            return 0
        if self._is_sorted_frontier_source(partial, stack):
            return 1
        return None

    def _eligible_dest(self, partial, sd: int, moved_group: int) -> bool:
        if partial.e(sd) <= 0 or partial.h(sd) == 0:
            return False
        if partial.is_sorted_stack(sd):
            return False
        if partial.sorted_n[sd] < self.min_dest_sorted_prefix:
            return False
        if self._bad_count(partial, sd) < self.min_dest_bad_suffix:
            return False
        dst_top = partial.g(sd)
        if self.require_strict_parking:
            return moved_group > dst_top
        return moved_group >= dst_top

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        kind = self._source_kind(partial, so)
        src_h = partial.h(so)
        dst_h = partial.h(sd)
        dst_top = partial.g(sd)
        moved = partial.g(so)
        src_bad = self._bad_count(partial, so)
        dst_bad = self._bad_count(partial, sd)
        kind_rank = kind
        if not self.prefer_single_blocker_source:
            kind_rank = 1 - kind if kind is not None else 2
        src_rank = src_h if self.prefer_shorter_source else -src_h
        dst_h_rank = -dst_h if self.prefer_taller_destination else dst_h
        dst_top_rank = dst_top if self.prefer_smaller_dest_top else -dst_top
        return (kind_rank, src_rank, dst_h_rank, dst_top_rank, -dst_bad, -moved, src_bad, so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            kind = self._source_kind(partial, action.so)
            if kind is None:
                continue
            moved_group = partial.g(action.so)
            if not self._eligible_dest(partial, action.sd, moved_group):
                continue
            allowed.append(action)
        if not allowed:
            return []
        return sorted(allowed, key=lambda a: self._sort_key(partial, a))

def build_component(problem, single_bad_count=1, frontier_max_height=2, min_source_sorted_prefix=1, min_dest_bad_suffix=1, min_dest_sorted_prefix=0, require_strict_parking=True, prefer_single_blocker_source=True, prefer_shorter_source=True, prefer_taller_destination=True, prefer_smaller_dest_top=True, **params):
    rule = FrontierBlockerToUnsortedParking(single_bad_count=single_bad_count, frontier_max_height=frontier_max_height, min_source_sorted_prefix=min_source_sorted_prefix, min_dest_bad_suffix=min_dest_bad_suffix, min_dest_sorted_prefix=min_dest_sorted_prefix, require_strict_parking=require_strict_parking, prefer_single_blocker_source=prefer_single_blocker_source, prefer_shorter_source=prefer_shorter_source, prefer_taller_destination=prefer_taller_destination, prefer_smaller_dest_top=prefer_smaller_dest_top)
    return RuleMachine(problem, [rule])
