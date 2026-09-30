from core.rules import RuleMachine
COMPONENT = {'name': 'sorted_source_consolidation', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'max_source_height': {'type': 'int', 'range': [1, 10], 'default': 3}, 'min_source_height': {'type': 'int', 'range': [1, 10], 'default': 1}, 'require_sorted_source': {'type': 'bool', 'default': True}, 'max_remaining_after_move': {'type': 'int', 'range': [0, 9], 'default': 1}, 'require_destination_sorted': {'type': 'bool', 'default': True}, 'allow_empty_destination': {'type': 'bool', 'default': False}, 'min_destination_height': {'type': 'int', 'range': [0, 10], 'default': 1}, 'require_safe_destination': {'type': 'bool', 'default': True}, 'prefer_tighter_group_fit': {'type': 'bool', 'default': True}}}

class SortedSourceConsolidation:
    """Consolida una fuente baja ya ordenada sobre un destino ordenado, preferiblemente liberando la fuente."""
    name = 'sorted_source_consolidation'

    def __init__(self, max_source_height: int, min_source_height: int, require_sorted_source: bool, max_remaining_after_move: int, require_destination_sorted: bool, allow_empty_destination: bool, min_destination_height: int, require_safe_destination: bool, prefer_free_source: bool, prefer_tighter_group_fit: bool, prefer_taller_destination: bool):
        self.max_source_height = int(max_source_height)
        self.min_source_height = int(min_source_height)
        self.require_sorted_source = bool(require_sorted_source)
        self.max_remaining_after_move = int(max_remaining_after_move)
        self.require_destination_sorted = bool(require_destination_sorted)
        self.allow_empty_destination = bool(allow_empty_destination)
        self.min_destination_height = int(min_destination_height)
        self.require_safe_destination = bool(require_safe_destination)
        self.prefer_free_source = bool(prefer_free_source)
        self.prefer_tighter_group_fit = bool(prefer_tighter_group_fit)
        self.prefer_taller_destination = bool(prefer_taller_destination)

    def _source_ok(self, partial, so: int) -> bool:
        hs = partial.h(so)
        if hs < self.min_source_height or hs > self.max_source_height:
            return False
        if hs == 0:
            return False
        if self.require_sorted_source and (not partial.is_sorted_stack(so)):
            return False
        return hs - 1 <= self.max_remaining_after_move

    def _destination_ok(self, partial, so: int, sd: int) -> bool:
        if partial.e(sd) <= 0:
            return False
        hd = partial.h(sd)
        if hd == 0:
            if not self.allow_empty_destination:
                return False
        elif hd < self.min_destination_height:
            return False
        if self.require_destination_sorted and (not partial.is_sorted_stack(sd)):
            return False
        moved_group = partial.g(so)
        if self.require_safe_destination and partial.g(sd) < moved_group:
            return False
        return True

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        hs = partial.h(so)
        hd = partial.h(sd)
        moved_group = partial.g(so)
        gap = partial.g(sd) - moved_group
        frees_source = hs == 1
        free_rank = 0 if self.prefer_free_source and frees_source else 1
        fit_rank = gap if self.prefer_tighter_group_fit else 0
        dest_rank = -hd if self.prefer_taller_destination else hd
        return (free_rank, hs - 1, fit_rank, dest_rank, so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if not self._source_ok(partial, so):
                continue
            if not self._destination_ok(partial, so, sd):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self._sort_key(partial, a))
        return allowed

def build_component(problem, max_source_height=3, min_source_height=1, require_sorted_source=True, max_remaining_after_move=1, require_destination_sorted=True, allow_empty_destination=False, min_destination_height=1, require_safe_destination=True, prefer_free_source=True, prefer_tighter_group_fit=True, prefer_taller_destination=True):
    rule = SortedSourceConsolidation(max_source_height=max_source_height, min_source_height=min_source_height, require_sorted_source=require_sorted_source, max_remaining_after_move=max_remaining_after_move, require_destination_sorted=require_destination_sorted, allow_empty_destination=allow_empty_destination, min_destination_height=min_destination_height, require_safe_destination=require_safe_destination, prefer_free_source=prefer_free_source, prefer_tighter_group_fit=prefer_tighter_group_fit, prefer_taller_destination=prefer_taller_destination)
    return RuleMachine(problem, [rule])
