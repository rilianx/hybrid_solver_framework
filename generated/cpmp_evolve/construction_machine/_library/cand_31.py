from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_to_unsorted_nonempty_buffer_parking', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_bad_suffix': {'type': 'int', 'range': [1, 10], 'default': 1}, 'max_source_height': {'type': 'int', 'range': [1, 10], 'default': 10}, 'min_dest_bad_suffix': {'type': 'int', 'range': [1, 10], 'default': 1}, 'min_dest_height': {'type': 'int', 'range': [1, 10], 'default': 1}, 'max_overshoot': {'type': 'int', 'range': [0, 50], 'default': 50}, 'prefer_taller_destination': {'type': 'bool', 'default': True}, 'prefer_smaller_overshoot': {'type': 'bool', 'default': True}}}

class UnsortedToUnsortedNonEmptyBufferParking:
    """Permite aparcar la cima de una fuente desordenada en un receptor no vacío y desordenado cuando no es un cap."""
    name = 'unsorted_to_unsorted_nonempty_buffer_parking'

    def __init__(self, min_source_bad_suffix: int, max_source_height: int, min_dest_bad_suffix: int, min_dest_height: int, max_overshoot: int, prefer_shorter_source: bool, prefer_taller_destination: bool, prefer_smaller_overshoot: bool, prefer_larger_source_bad_suffix: bool):
        self.min_source_bad_suffix = int(min_source_bad_suffix)
        self.max_source_height = int(max_source_height)
        self.min_dest_bad_suffix = int(min_dest_bad_suffix)
        self.min_dest_height = int(min_dest_height)
        self.max_overshoot = int(max_overshoot)
        self.prefer_shorter_source = bool(prefer_shorter_source)
        self.prefer_taller_destination = bool(prefer_taller_destination)
        self.prefer_smaller_overshoot = bool(prefer_smaller_overshoot)
        self.prefer_larger_source_bad_suffix = bool(prefer_larger_source_bad_suffix)

    def _bad_count(self, partial, stack: int) -> int:
        return partial.h(stack) - partial.sorted_n[stack]

    def _eligible_source(self, partial, so: int) -> bool:
        if partial.h(so) == 0:
            return False
        if partial.h(so) > self.max_source_height:
            return False
        if partial.is_sorted_stack(so):
            return False
        return self._bad_count(partial, so) >= self.min_source_bad_suffix

    def _eligible_dest(self, partial, sd: int, moved_group: int) -> bool:
        if partial.e(sd) <= 0:
            return False
        if partial.h(sd) < self.min_dest_height:
            return False
        if partial.h(sd) == 0:
            return False
        if partial.is_sorted_stack(sd):
            return False
        if self._bad_count(partial, sd) < self.min_dest_bad_suffix:
            return False
        dest_top = partial.g(sd)
        if moved_group <= dest_top:
            return False
        return moved_group - dest_top <= self.max_overshoot

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved_group = partial.g(so)
        source_height = partial.h(so)
        source_bad = self._bad_count(partial, so)
        dest_height = partial.h(sd)
        dest_top = partial.g(sd)
        overshoot = moved_group - dest_top
        source_height_rank = source_height if self.prefer_shorter_source else -source_height
        dest_height_rank = -dest_height if self.prefer_taller_destination else dest_height
        overshoot_rank = overshoot if self.prefer_smaller_overshoot else -overshoot
        source_bad_rank = -source_bad if self.prefer_larger_source_bad_suffix else source_bad
        return (source_height_rank, dest_height_rank, overshoot_rank, source_bad_rank, so, sd)

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

def build_component(problem, min_source_bad_suffix=1, max_source_height=10, min_dest_bad_suffix=1, min_dest_height=1, max_overshoot=50, prefer_shorter_source=True, prefer_taller_destination=True, prefer_smaller_overshoot=True, prefer_larger_source_bad_suffix=True, **params):
    rule = UnsortedToUnsortedNonEmptyBufferParking(min_source_bad_suffix=min_source_bad_suffix, max_source_height=max_source_height, min_dest_bad_suffix=min_dest_bad_suffix, min_dest_height=min_dest_height, max_overshoot=max_overshoot, prefer_shorter_source=prefer_shorter_source, prefer_taller_destination=prefer_taller_destination, prefer_smaller_overshoot=prefer_smaller_overshoot, prefer_larger_source_bad_suffix=prefer_larger_source_bad_suffix)
    return RuleMachine(problem, [rule])
