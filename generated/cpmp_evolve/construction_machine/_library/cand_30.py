from core.rules import RuleMachine
COMPONENT = {'name': 'prefix_capped_unsorted_receiver', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_dest_sorted_prefix': {'type': 'int', 'range': [1, 10], 'default': 2}, 'min_source_bad_suffix': {'type': 'int', 'range': [1, 10], 'default': 1}, 'prefer_tighter_cap': {'type': 'bool', 'default': True}}}

class PrefixCappedUnsortedReceiver:
    """Permite solo capar un destino desordenado con buen prefijo ordenado usando una cima que no supera la cima actual."""
    name = 'prefix_capped_unsorted_receiver'

    def __init__(self, min_dest_sorted_prefix: int, min_source_bad_suffix: int, require_unsorted_source: bool, prefer_longer_dest_prefix: bool, prefer_tighter_cap: bool, prefer_peeling_shorter_source: bool):
        self.min_dest_sorted_prefix = int(min_dest_sorted_prefix)
        self.min_source_bad_suffix = int(min_source_bad_suffix)
        self.require_unsorted_source = bool(require_unsorted_source)
        self.prefer_longer_dest_prefix = bool(prefer_longer_dest_prefix)
        self.prefer_tighter_cap = bool(prefer_tighter_cap)
        self.prefer_peeling_shorter_source = bool(prefer_peeling_shorter_source)

    def _bad_count(self, partial, stack: int) -> int:
        return partial.h(stack) - partial.sorted_n[stack]

    def _eligible_source(self, partial, so: int) -> bool:
        if partial.h(so) == 0:
            return False
        if self.require_unsorted_source and partial.is_sorted_stack(so):
            return False
        return self._bad_count(partial, so) >= self.min_source_bad_suffix

    def _eligible_dest(self, partial, sd: int, moved_group: int) -> bool:
        if partial.e(sd) <= 0:
            return False
        if partial.h(sd) == 0:
            return False
        if partial.is_sorted_stack(sd):
            return False
        if partial.sorted_n[sd] < self.min_dest_sorted_prefix:
            return False
        return moved_group <= partial.g(sd)

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved_group = partial.g(so)
        dest_top = partial.g(sd)
        dest_prefix = partial.sorted_n[sd]
        source_height = partial.h(so)
        source_bad = self._bad_count(partial, so)
        cap_gap = dest_top - moved_group
        prefix_rank = -dest_prefix if self.prefer_longer_dest_prefix else dest_prefix
        gap_rank = cap_gap if self.prefer_tighter_cap else -cap_gap
        source_rank = source_height if self.prefer_peeling_shorter_source else -source_height
        return (prefix_rank, gap_rank, source_rank, -source_bad, so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if not self._eligible_source(partial, so):
                continue
            if not self._eligible_dest(partial, sd, partial.g(so)):
                continue
            allowed.append(action)
        if not allowed:
            return []
        return sorted(allowed, key=lambda a: self._sort_key(partial, a))

def build_component(problem, min_dest_sorted_prefix=2, min_source_bad_suffix=1, require_unsorted_source=True, prefer_longer_dest_prefix=True, prefer_tighter_cap=True, prefer_peeling_shorter_source=True, **params):
    rule = PrefixCappedUnsortedReceiver(min_dest_sorted_prefix=min_dest_sorted_prefix, min_source_bad_suffix=min_source_bad_suffix, require_unsorted_source=require_unsorted_source, prefer_longer_dest_prefix=prefer_longer_dest_prefix, prefer_tighter_cap=prefer_tighter_cap, prefer_peeling_shorter_source=prefer_peeling_shorter_source)
    return RuleMachine(problem, [rule])
