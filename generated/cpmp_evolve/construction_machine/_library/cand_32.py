from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_to_unsorted_top_cap', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_bad': {'type': 'int', 'range': [1, 6], 'default': 1}, 'min_dest_bad': {'type': 'int', 'range': [1, 6], 'default': 1}, 'min_dest_height': {'type': 'int', 'range': [1, 6], 'default': 2}, 'prefer_tighter_cap': {'type': 'bool', 'default': True}}}

class UnsortedToUnsortedTopCapRule:
    """Permite mover la cima de una fuente desordenada para capar por arriba un destino desordenado manteniendo decreciente el sufijo superior."""
    name = 'unsorted_to_unsorted_top_cap'

    def __init__(self, min_source_bad: int, min_dest_bad: int, min_dest_height: int, require_strict_drop: bool, prefer_exposes_sorted_source: bool, prefer_longer_dest_sorted_prefix: bool, prefer_tighter_cap: bool):
        self.min_source_bad = int(min_source_bad)
        self.min_dest_bad = int(min_dest_bad)
        self.min_dest_height = int(min_dest_height)
        self.require_strict_drop = bool(require_strict_drop)
        self.prefer_exposes_sorted_source = bool(prefer_exposes_sorted_source)
        self.prefer_longer_dest_sorted_prefix = bool(prefer_longer_dest_sorted_prefix)
        self.prefer_tighter_cap = bool(prefer_tighter_cap)

    def _bad_count(self, partial, s):
        return partial.h(s) - partial.sorted_n[s]

    def _source_ok(self, partial, so):
        return partial.h(so) > 0 and self._bad_count(partial, so) >= self.min_source_bad

    def _dest_ok(self, partial, sd):
        return partial.e(sd) > 0 and partial.h(sd) >= self.min_dest_height and (self._bad_count(partial, sd) >= self.min_dest_bad)

    def _cap_ok(self, partial, so, sd):
        moved = partial.g(so)
        dst_top = partial.g(sd)
        if self.require_strict_drop:
            return moved < dst_top
        return moved <= dst_top

    def _exposes_sorted_source(self, partial, so):
        return partial.h(so) > 0 and self._bad_count(partial, so) == 1 and (partial.sorted_n[so] > 0)

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved = partial.g(so)
        dst_top = partial.g(sd)
        expose_rank = 0 if self.prefer_exposes_sorted_source and self._exposes_sorted_source(partial, so) else 1
        dest_prefix_rank = -partial.sorted_n[sd] if self.prefer_longer_dest_sorted_prefix else partial.sorted_n[sd]
        cap_gap_rank = dst_top - moved if self.prefer_tighter_cap else -(dst_top - moved)
        return (expose_rank, dest_prefix_rank, cap_gap_rank, -partial.h(sd), self._bad_count(partial, so), so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if not self._source_ok(partial, so):
                continue
            if not self._dest_ok(partial, sd):
                continue
            if not self._cap_ok(partial, so, sd):
                continue
            allowed.append(action)
        return sorted(allowed, key=lambda a: self._sort_key(partial, a))

def build_component(problem, min_source_bad=1, min_dest_bad=1, min_dest_height=2, require_strict_drop=True, prefer_exposes_sorted_source=True, prefer_longer_dest_sorted_prefix=True, prefer_tighter_cap=True, **params):
    rule = UnsortedToUnsortedTopCapRule(min_source_bad=min_source_bad, min_dest_bad=min_dest_bad, min_dest_height=min_dest_height, require_strict_drop=require_strict_drop, prefer_exposes_sorted_source=prefer_exposes_sorted_source, prefer_longer_dest_sorted_prefix=prefer_longer_dest_sorted_prefix, prefer_tighter_cap=prefer_tighter_cap)
    return RuleMachine(problem, [rule])
