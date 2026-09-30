from core.rules import RuleMachine
COMPONENT = {'name': 'short_sorted_release_to_unsorted_receiver', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_height': {'type': 'int', 'range': [1, 4], 'default': 1}, 'min_dest_bad_suffix': {'type': 'int', 'range': [1, 6], 'default': 1}, 'require_freeing_source': {'type': 'bool', 'default': True}, 'prefer_taller_unsorted_dest': {'type': 'bool', 'default': True}, 'prefer_higher_moved_group': {'type': 'bool', 'default': True}}}

class ShortSortedReleaseToUnsortedReceiver:
    """Permite liberar una pila fuente corta y ya ordenada moviendo su cima a una pila destino ya desordenada y no vacía."""
    name = 'short_sorted_release_to_unsorted_receiver'

    def __init__(self, max_source_height: int, min_source_height: int, min_dest_bad_suffix: int, require_freeing_source: bool, prefer_taller_unsorted_dest: bool, prefer_higher_moved_group: bool, prefer_shorter_source: bool):
        self.max_source_height = int(max_source_height)
        self.min_source_height = int(min_source_height)
        self.min_dest_bad_suffix = int(min_dest_bad_suffix)
        self.require_freeing_source = bool(require_freeing_source)
        self.prefer_taller_unsorted_dest = bool(prefer_taller_unsorted_dest)
        self.prefer_higher_moved_group = bool(prefer_higher_moved_group)
        self.prefer_shorter_source = bool(prefer_shorter_source)

    def _dest_bad_suffix(self, partial, sd: int) -> int:
        return partial.h(sd) - partial.sorted_n[sd]

    def _eligible_source(self, partial, so: int) -> bool:
        h = partial.h(so)
        if h < self.min_source_height or h > self.max_source_height:
            return False
        if not partial.is_sorted_stack(so):
            return False
        if self.require_freeing_source and h != 1:
            return False
        return True

    def _eligible_dest(self, partial, sd: int) -> bool:
        if partial.e(sd) <= 0:
            return False
        if partial.h(sd) == 0:
            return False
        if partial.is_sorted_stack(sd):
            return False
        return self._dest_bad_suffix(partial, sd) >= self.min_dest_bad_suffix

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        source_height = partial.h(so)
        moved_group = partial.g(so)
        dest_height = partial.h(sd)
        dest_bad = self._dest_bad_suffix(partial, sd)
        dest_top = partial.g(sd)
        source_rank = source_height if self.prefer_shorter_source else -source_height
        moved_rank = -moved_group if self.prefer_higher_moved_group else moved_group
        dest_height_rank = -dest_height if self.prefer_taller_unsorted_dest else dest_height
        return (source_rank, moved_rank, dest_height_rank, -dest_bad, abs(dest_top - moved_group), so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            if not self._eligible_source(partial, action.so):
                continue
            if not self._eligible_dest(partial, action.sd):
                continue
            allowed.append(action)
        if not allowed:
            return []
        return sorted(allowed, key=lambda a: self._sort_key(partial, a))

def build_component(problem, max_source_height=2, min_source_height=1, min_dest_bad_suffix=1, require_freeing_source=True, prefer_taller_unsorted_dest=True, prefer_higher_moved_group=True, prefer_shorter_source=True, **params):
    rule = ShortSortedReleaseToUnsortedReceiver(max_source_height=max_source_height, min_source_height=min_source_height, min_dest_bad_suffix=min_dest_bad_suffix, require_freeing_source=require_freeing_source, prefer_taller_unsorted_dest=prefer_taller_unsorted_dest, prefer_higher_moved_group=prefer_higher_moved_group, prefer_shorter_source=prefer_shorter_source)
    return RuleMachine(problem, [rule])
