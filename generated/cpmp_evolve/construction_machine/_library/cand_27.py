COMPONENT = {'name': 'sorted_to_sorted_safe_consolidation_strict', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'max_source_height': {'type': 'int', 'range': [1, 10], 'default': 3}, 'min_source_height': {'type': 'int', 'range': [1, 10], 'default': 1}, 'require_source_sorted': {'type': 'bool', 'default': True}, 'prefer_freeing_source': {'type': 'bool', 'default': True}, 'prefer_tighter_group_fit': {'type': 'bool', 'default': True}}}
from core.rules import RuleMachine

class SortedToSortedSafeConsolidationStrict:
    """Permite consolidar moviendo de una pila fuente ordenada y baja a una pila destino ordenada sin desordenar el destino."""
    name = 'sorted_to_sorted_safe_consolidation_strict'

    def __init__(self, max_source_height: int, min_source_height: int, require_source_sorted: bool, prefer_freeing_source: bool, prefer_non_empty_destination: bool, prefer_tighter_group_fit: bool, prefer_taller_sorted_destination: bool):
        self.max_source_height = int(max_source_height)
        self.min_source_height = int(min_source_height)
        self.require_source_sorted = bool(require_source_sorted)
        self.prefer_freeing_source = bool(prefer_freeing_source)
        self.prefer_non_empty_destination = bool(prefer_non_empty_destination)
        self.prefer_tighter_group_fit = bool(prefer_tighter_group_fit)
        self.prefer_taller_sorted_destination = bool(prefer_taller_sorted_destination)

    def _source_ok(self, partial, so):
        h = partial.h(so)
        if h < self.min_source_height or h > self.max_source_height:
            return False
        if h == 0:
            return False
        if self.require_source_sorted and (not partial.is_sorted_stack(so)):
            return False
        return True

    def _dest_ok(self, partial, so, sd):
        if so == sd:
            return False
        if partial.e(sd) <= 0:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved_group = partial.g(so)
        src_height = partial.h(so)
        dst_height = partial.h(sd)
        dst_top = partial.g(sd)
        frees_source_rank = 0 if self.prefer_freeing_source and src_height == 1 else 1
        non_empty_dest_rank = 0 if self.prefer_non_empty_destination and dst_height > 0 else 1
        tighter_fit = abs(dst_top - moved_group) if self.prefer_tighter_group_fit else 0
        taller_dest_rank = -dst_height if self.prefer_taller_sorted_destination else dst_height
        return (frees_source_rank, non_empty_dest_rank, tighter_fit, taller_dest_rank, src_height, so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            if not self._source_ok(partial, action.so):
                continue
            if not self._dest_ok(partial, action.so, action.sd):
                continue
            allowed.append(action)
        return sorted(allowed, key=lambda a: self._sort_key(partial, a))

def build_component(problem, max_source_height=3, min_source_height=1, require_source_sorted=True, prefer_freeing_source=True, prefer_non_empty_destination=True, prefer_tighter_group_fit=True, prefer_taller_sorted_destination=True, **params):
    rule = SortedToSortedSafeConsolidationStrict(max_source_height=max_source_height, min_source_height=min_source_height, require_source_sorted=require_source_sorted, prefer_freeing_source=prefer_freeing_source, prefer_non_empty_destination=prefer_non_empty_destination, prefer_tighter_group_fit=prefer_tighter_group_fit, prefer_taller_sorted_destination=prefer_taller_sorted_destination)
    return RuleMachine(problem, [rule])
