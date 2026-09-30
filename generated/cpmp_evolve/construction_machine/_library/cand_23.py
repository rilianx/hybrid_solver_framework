COMPONENT = {'name': 'forced_single_blocker_to_empty_buffer', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_sorted_prefix': {'type': 'int', 'range': [1, 8], 'default': 1}}}
from core.rules import RuleMachine

class ForcedSingleBlockerToEmptyBuffer:
    """Mueve a una pila vacía el bloqueador único de una fuente casi ordenada solo si no existe destino seguro no vacío."""
    name = 'forced_single_blocker_to_empty_buffer'

    def __init__(self, max_source_height: int, min_sorted_prefix: int, require_exposed_sorted_stack: bool, prefer_shorter_source: bool, prefer_taller_exposed_prefix: bool, prefer_lower_moved_group: bool):
        self.max_source_height = int(max_source_height)
        self.min_sorted_prefix = int(min_sorted_prefix)
        self.require_exposed_sorted_stack = bool(require_exposed_sorted_stack)
        self.prefer_shorter_source = bool(prefer_shorter_source)
        self.prefer_taller_exposed_prefix = bool(prefer_taller_exposed_prefix)
        self.prefer_lower_moved_group = bool(prefer_lower_moved_group)

    def _bad_count(self, partial, s: int) -> int:
        return partial.h(s) - partial.sorted_n[s]

    def _is_single_blocker_source(self, partial, s: int) -> bool:
        h = partial.h(s)
        if h <= 1 or h > self.max_source_height:
            return False
        if self._bad_count(partial, s) != 1:
            return False
        if partial.sorted_n[s] < self.min_sorted_prefix:
            return False
        if self.require_exposed_sorted_stack and partial.sorted_n[s] != h - 1:
            return False
        return True

    def _has_safe_non_empty_destination(self, partial, so: int, candidates) -> bool:
        moved_group = partial.g(so)
        for action in candidates:
            if action.so != so:
                continue
            sd = action.sd
            if partial.h(sd) == 0 or partial.e(sd) <= 0:
                continue
            if partial.is_sorted_stack(sd) and partial.g(sd) >= moved_group:
                return True
        return False

    def _sort_key(self, partial, action):
        so = action.so
        source_height = partial.h(so)
        exposed_prefix = partial.sorted_n[so]
        moved_group = partial.g(so)
        k1 = source_height if self.prefer_shorter_source else -source_height
        k2 = -exposed_prefix if self.prefer_taller_exposed_prefix else exposed_prefix
        k3 = moved_group if self.prefer_lower_moved_group else -moved_group
        return (k1, k2, k3, so, action.sd)

    def allowed(self, partial, memory, candidates):
        empty_dests = {a.sd for a in candidates if partial.h(a.sd) == 0 and partial.e(a.sd) > 0}
        if not empty_dests:
            return []
        feasible_sources = []
        seen = set()
        for action in candidates:
            so = action.so
            if so in seen:
                continue
            seen.add(so)
            if not self._is_single_blocker_source(partial, so):
                continue
            if self._has_safe_non_empty_destination(partial, so, candidates):
                continue
            feasible_sources.append(so)
        if not feasible_sources:
            return []
        allowed = [action for action in candidates if action.so in feasible_sources and partial.h(action.sd) == 0 and (partial.e(action.sd) > 0)]
        allowed.sort(key=lambda action: self._sort_key(partial, action))
        return allowed

def build_component(problem, max_source_height=4, min_sorted_prefix=1, require_exposed_sorted_stack=True, prefer_shorter_source=True, prefer_taller_exposed_prefix=True, prefer_lower_moved_group=True):
    rule = ForcedSingleBlockerToEmptyBuffer(max_source_height=max_source_height, min_sorted_prefix=min_sorted_prefix, require_exposed_sorted_stack=require_exposed_sorted_stack, prefer_shorter_source=prefer_shorter_source, prefer_taller_exposed_prefix=prefer_taller_exposed_prefix, prefer_lower_moved_group=prefer_lower_moved_group)
    return RuleMachine(problem, [rule])
