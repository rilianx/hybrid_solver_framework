from core.rules import RuleMachine
COMPONENT = {'name': 'necessary_sorted_release_to_empty_buffer', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_height': {'type': 'int', 'range': [1, 10], 'default': 1}, 'min_sorted_prefix': {'type': 'int', 'range': [1, 10], 'default': 1}, 'require_sorted_source': {'type': 'bool', 'default': True}}}

class NecessarySortedReleaseToEmptyBuffer:
    """Libera una fuente ordenada hacia un buffer vacío solo cuando no hay destino seguro no vacío."""
    name = 'necessary_sorted_release_to_empty_buffer'

    def __init__(self, min_source_height: int, max_source_height: int, min_sorted_prefix: int, require_sorted_source: bool, require_no_safe_nonempty_destination: bool, prefer_freeing_source: bool, prefer_shorter_source: bool, prefer_lower_group_to_buffer: bool):
        self.min_source_height = int(min_source_height)
        self.max_source_height = int(max_source_height)
        self.min_sorted_prefix = int(min_sorted_prefix)
        self.require_sorted_source = bool(require_sorted_source)
        self.require_no_safe_nonempty_destination = bool(require_no_safe_nonempty_destination)
        self.prefer_freeing_source = bool(prefer_freeing_source)
        self.prefer_shorter_source = bool(prefer_shorter_source)
        self.prefer_lower_group_to_buffer = bool(prefer_lower_group_to_buffer)

    def _source_ok(self, partial, so: int) -> bool:
        h = partial.h(so)
        if h < self.min_source_height or h > self.max_source_height:
            return False
        if partial.sorted_n[so] < self.min_sorted_prefix:
            return False
        if self.require_sorted_source and (not partial.is_sorted_stack(so)):
            return False
        return h > 0

    def _keeps_destination_sorted_nonempty(self, partial, so: int, sd: int) -> bool:
        return so != sd and partial.h(sd) > 0 and (partial.e(sd) > 0) and partial.is_sorted_stack(sd) and (partial.g(sd) >= partial.g(so))

    def _has_safe_nonempty_destination(self, partial, so: int, candidates) -> bool:
        for action in candidates:
            if action.so != so:
                continue
            if self._keeps_destination_sorted_nonempty(partial, so, action.sd):
                return True
        return False

    def _action_ok(self, partial, candidates, action) -> bool:
        so = action.so
        sd = action.sd
        if partial.h(sd) != 0:
            return False
        if partial.e(sd) <= 0:
            return False
        if not self._source_ok(partial, so):
            return False
        if self.require_no_safe_nonempty_destination and self._has_safe_nonempty_destination(partial, so, candidates):
            return False
        return True

    def _key(self, partial, action):
        so = action.so
        frees_source = partial.h(so) == 1
        source_height = partial.h(so)
        moved_group = partial.g(so)
        free_rank = 0 if self.prefer_freeing_source and frees_source else 1 if self.prefer_freeing_source else 0
        height_rank = source_height if self.prefer_shorter_source else -source_height
        group_rank = moved_group if self.prefer_lower_group_to_buffer else -moved_group
        return (free_rank, height_rank, group_rank, so, action.sd)

    def allowed(self, partial, memory, candidates):
        allowed = [action for action in candidates if self._action_ok(partial, candidates, action)]
        allowed.sort(key=lambda action: self._key(partial, action))
        return allowed

def build_component(problem, min_source_height=1, max_source_height=3, min_sorted_prefix=1, require_sorted_source=True, require_no_safe_nonempty_destination=True, prefer_freeing_source=True, prefer_shorter_source=True, prefer_lower_group_to_buffer=True):
    rule = NecessarySortedReleaseToEmptyBuffer(min_source_height=min_source_height, max_source_height=max_source_height, min_sorted_prefix=min_sorted_prefix, require_sorted_source=require_sorted_source, require_no_safe_nonempty_destination=require_no_safe_nonempty_destination, prefer_freeing_source=prefer_freeing_source, prefer_shorter_source=prefer_shorter_source, prefer_lower_group_to_buffer=prefer_lower_group_to_buffer)
    return RuleMachine(problem, [rule])
