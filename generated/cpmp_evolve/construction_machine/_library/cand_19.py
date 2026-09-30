from core.rules import RuleMachine
COMPONENT = {'name': 'sorted_to_sorted_safe_consolidation', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_height': {'type': 'int', 'range': [1, 10], 'default': 1}, 'require_free_source': {'type': 'bool', 'default': True}}}

class SortedToSortedSafeConsolidation:
    """Permite consolidar moviendo desde una fuente ya ordenada a un destino ya ordenado sin desordenar el destino."""
    name = 'sorted_to_sorted_safe_consolidation'

    def __init__(self, max_source_height: int, min_source_height: int, require_free_source: bool, prefer_non_empty_destination: bool, prefer_tighter_group_fit: bool, prefer_taller_destination: bool):
        self.max_source_height = int(max_source_height)
        self.min_source_height = int(min_source_height)
        self.require_free_source = bool(require_free_source)
        self.prefer_non_empty_destination = bool(prefer_non_empty_destination)
        self.prefer_tighter_group_fit = bool(prefer_tighter_group_fit)
        self.prefer_taller_destination = bool(prefer_taller_destination)

    def _source_ok(self, partial, so: int) -> bool:
        height = partial.h(so)
        if height < self.min_source_height or height > self.max_source_height:
            return False
        if not partial.is_sorted_stack(so):
            return False
        if self.require_free_source and height != 1:
            return False
        return True

    def _dest_ok(self, partial, so: int, sd: int) -> bool:
        if so == sd:
            return False
        if partial.e(sd) <= 0:
            return False
        if partial.h(sd) == 0:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved_group = partial.g(so)
        dest_top = partial.g(sd)
        gap = dest_top - moved_group
        dest_empty = partial.h(sd) == 0
        dest_height = partial.h(sd)
        source_height = partial.h(so)
        key = []
        if self.prefer_non_empty_destination:
            key.append(dest_empty)
        if self.prefer_tighter_group_fit:
            key.append(gap)
        if self.prefer_taller_destination:
            key.append(-dest_height)
        key.extend([source_height, -partial.sorted_n[sd], so, sd])
        return tuple(key)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            if not self._source_ok(partial, action.so):
                continue
            if not self._dest_ok(partial, action.so, action.sd):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self._sort_key(partial, a))
        return allowed

def build_component(problem, max_source_height=3, min_source_height=1, require_free_source=True, prefer_non_empty_destination=True, prefer_tighter_group_fit=True, prefer_taller_destination=True):
    rule = SortedToSortedSafeConsolidation(max_source_height=max_source_height, min_source_height=min_source_height, require_free_source=require_free_source, prefer_non_empty_destination=prefer_non_empty_destination, prefer_tighter_group_fit=prefer_tighter_group_fit, prefer_taller_destination=prefer_taller_destination)
    return RuleMachine(problem, [rule])
