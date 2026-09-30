from core.rules import RuleMachine
COMPONENT = {'name': 'necessary_single_blocker_to_empty_buffer', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'required_bad_count': {'type': 'int', 'range': [1, 2], 'default': 1}, 'min_sorted_prefix': {'type': 'int', 'range': [0, 10], 'default': 1}, 'min_source_height': {'type': 'int', 'range': [1, 10], 'default': 2}, 'max_source_height': {'type': 'int', 'range': [1, 10], 'default': 10}}}

class NecessarySingleBlockerToEmptyBuffer:
    """Permite mover al buffer vacío solo el único bloqueador superior cuando no hay destino ordenado no vacío seguro."""
    name = 'necessary_single_blocker_to_empty_buffer'

    def __init__(self, required_bad_count: int, min_sorted_prefix: int, min_source_height: int, max_source_height: int, prefer_taller_source: bool, prefer_more_exposed_sorted_prefix: bool):
        self.required_bad_count = int(required_bad_count)
        self.min_sorted_prefix = int(min_sorted_prefix)
        self.min_source_height = int(min_source_height)
        self.max_source_height = int(max_source_height)
        self.prefer_taller_source = bool(prefer_taller_source)
        self.prefer_more_exposed_sorted_prefix = bool(prefer_more_exposed_sorted_prefix)

    def _bad_count(self, partial, stack: int) -> int:
        return partial.h(stack) - partial.sorted_n[stack]

    def _is_eligible_source(self, partial, so: int) -> bool:
        h = partial.h(so)
        if h < self.min_source_height or h > self.max_source_height:
            return False
        if h == 0:
            return False
        if partial.is_sorted_stack(so):
            return False
        if self._bad_count(partial, so) != self.required_bad_count:
            return False
        if partial.sorted_n[so] < self.min_sorted_prefix:
            return False
        return True

    def _has_safe_nonempty_sorted_destination(self, partial, so: int, candidates) -> bool:
        moved_group = partial.g(so)
        for action in candidates:
            if action.so != so:
                continue
            sd = action.sd
            if partial.h(sd) == 0:
                continue
            if partial.e(sd) <= 0:
                continue
            if partial.is_sorted_stack(sd) and partial.g(sd) >= moved_group:
                return True
        return False

    def _sort_key(self, partial, action):
        so = action.so
        src_h = partial.h(so)
        src_sorted = partial.sorted_n[so]
        source_height_key = -src_h if self.prefer_taller_source else src_h
        source_prefix_key = -src_sorted if self.prefer_more_exposed_sorted_prefix else src_sorted
        return (source_height_key, source_prefix_key, partial.g(so), so, action.sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if partial.h(sd) != 0:
                continue
            if partial.e(sd) <= 0:
                continue
            if not self._is_eligible_source(partial, so):
                continue
            if self._has_safe_nonempty_sorted_destination(partial, so, candidates):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self._sort_key(partial, a))
        return allowed

def build_component(problem, required_bad_count=1, min_sorted_prefix=1, min_source_height=2, max_source_height=10, prefer_taller_source=True, prefer_more_exposed_sorted_prefix=True):
    rule = NecessarySingleBlockerToEmptyBuffer(required_bad_count=required_bad_count, min_sorted_prefix=min_sorted_prefix, min_source_height=min_source_height, max_source_height=max_source_height, prefer_taller_source=prefer_taller_source, prefer_more_exposed_sorted_prefix=prefer_more_exposed_sorted_prefix)
    return RuleMachine(problem, [rule])
