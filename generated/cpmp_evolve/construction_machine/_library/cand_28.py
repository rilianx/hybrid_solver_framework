from core.rules import RuleMachine
COMPONENT = {'name': 'single_blocker_to_unsorted_cap', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_sorted_prefix': {'type': 'int', 'range': [1, 6], 'default': 2}, 'min_dest_sorted_prefix': {'type': 'int', 'range': [1, 6], 'default': 2}}}

class SingleBlockerToUnsortedCapRule:
    """Permite mover el bloqueador superior de una fuente casi ordenada a un destino desordenado cuyo tope lo puede capar."""
    name = 'single_blocker_to_unsorted_cap'

    def __init__(self, source_bad_count: int, min_source_sorted_prefix: int, max_source_height: int, min_dest_sorted_prefix: int, max_dest_bad_count: int, prefer_source_becomes_sorted: bool, prefer_tighter_cap: bool, prefer_taller_dest: bool):
        self.source_bad_count = int(source_bad_count)
        self.min_source_sorted_prefix = int(min_source_sorted_prefix)
        self.max_source_height = int(max_source_height)
        self.min_dest_sorted_prefix = int(min_dest_sorted_prefix)
        self.max_dest_bad_count = int(max_dest_bad_count)
        self.prefer_source_becomes_sorted = bool(prefer_source_becomes_sorted)
        self.prefer_tighter_cap = bool(prefer_tighter_cap)
        self.prefer_taller_dest = bool(prefer_taller_dest)

    def _bad_count(self, partial, s: int) -> int:
        return partial.h(s) - partial.sorted_n[s]

    def _source_ok(self, partial, s: int) -> bool:
        h = partial.h(s)
        if h <= 0 or h > self.max_source_height:
            return False
        if partial.is_sorted_stack(s):
            return False
        if self._bad_count(partial, s) != self.source_bad_count:
            return False
        return partial.sorted_n[s] >= self.min_source_sorted_prefix

    def _dest_ok(self, partial, s: int, moved_group: int) -> bool:
        if partial.e(s) <= 0 or partial.h(s) == 0:
            return False
        if partial.is_sorted_stack(s):
            return False
        if partial.sorted_n[s] < self.min_dest_sorted_prefix:
            return False
        if self._bad_count(partial, s) > self.max_dest_bad_count:
            return False
        return partial.g(s) >= moved_group

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved = partial.g(so)
        src_h = partial.h(so)
        dst_h = partial.h(sd)
        dst_top = partial.g(sd)
        src_prefix = partial.sorted_n[so]
        dst_prefix = partial.sorted_n[sd]
        source_becomes_sorted = self._bad_count(partial, so) == 1
        cap_gap = dst_top - moved
        source_rank = not source_becomes_sorted if self.prefer_source_becomes_sorted else source_becomes_sorted
        cap_rank = cap_gap if self.prefer_tighter_cap else -cap_gap
        dest_height_rank = -dst_h if self.prefer_taller_dest else dst_h
        return (source_rank, cap_rank, dest_height_rank, -dst_prefix, src_h, -src_prefix, so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if so == sd:
                continue
            if not self._source_ok(partial, so):
                continue
            moved_group = partial.g(so)
            if not self._dest_ok(partial, sd, moved_group):
                continue
            allowed.append(action)
        return sorted(allowed, key=lambda a: self._sort_key(partial, a))

def build_component(problem, source_bad_count=1, min_source_sorted_prefix=2, max_source_height=6, min_dest_sorted_prefix=2, max_dest_bad_count=4, prefer_source_becomes_sorted=True, prefer_tighter_cap=True, prefer_taller_dest=True, **params):
    rule = SingleBlockerToUnsortedCapRule(source_bad_count=source_bad_count, min_source_sorted_prefix=min_source_sorted_prefix, max_source_height=max_source_height, min_dest_sorted_prefix=min_dest_sorted_prefix, max_dest_bad_count=max_dest_bad_count, prefer_source_becomes_sorted=prefer_source_becomes_sorted, prefer_tighter_cap=prefer_tighter_cap, prefer_taller_dest=prefer_taller_dest)
    return RuleMachine(problem, [rule])
