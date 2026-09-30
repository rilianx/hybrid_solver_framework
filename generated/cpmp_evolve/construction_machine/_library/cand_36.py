from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_to_unsorted_bad_suffix_parking', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_bad_suffix': {'type': 'int', 'range': [1, 6], 'default': 2}, 'min_dest_bad_suffix': {'type': 'int', 'range': [1, 6], 'default': 1}, 'min_dest_sorted_prefix': {'type': 'int', 'range': [0, 6], 'default': 0}, 'max_dest_sorted_prefix': {'type': 'int', 'range': [0, 6], 'default': 1}, 'prefer_larger_parking_gap': {'type': 'bool', 'default': True}}}

class UnsortedToUnsortedBadSuffixParking:
    """Permite aparcar la cima de una fuente desordenada sobre un destino ya desordenado y no vacío, empeorando solo su sufijo malo."""
    name = 'unsorted_to_unsorted_bad_suffix_parking'

    def __init__(self, min_source_bad_suffix: int, min_dest_bad_suffix: int, min_dest_sorted_prefix: int, max_dest_sorted_prefix: int, require_nonempty_dest: bool, require_strictly_worse_than_dest_top: bool, prefer_shorter_dest_prefix: bool, prefer_taller_dest: bool, prefer_larger_parking_gap: bool, prefer_shorter_source: bool):
        self.min_source_bad_suffix = int(min_source_bad_suffix)
        self.min_dest_bad_suffix = int(min_dest_bad_suffix)
        self.min_dest_sorted_prefix = int(min_dest_sorted_prefix)
        self.max_dest_sorted_prefix = int(max_dest_sorted_prefix)
        self.require_nonempty_dest = bool(require_nonempty_dest)
        self.require_strictly_worse_than_dest_top = bool(require_strictly_worse_than_dest_top)
        self.prefer_shorter_dest_prefix = bool(prefer_shorter_dest_prefix)
        self.prefer_taller_dest = bool(prefer_taller_dest)
        self.prefer_larger_parking_gap = bool(prefer_larger_parking_gap)
        self.prefer_shorter_source = bool(prefer_shorter_source)

    def _bad_count(self, partial, s: int) -> int:
        return partial.h(s) - partial.sorted_n[s]

    def _source_ok(self, partial, so: int) -> bool:
        return partial.h(so) > 0 and (not partial.is_sorted_stack(so)) and (self._bad_count(partial, so) >= self.min_source_bad_suffix)

    def _dest_ok(self, partial, sd: int, moved_group: int) -> bool:
        if partial.e(sd) <= 0:
            return False
        if self.require_nonempty_dest and partial.h(sd) == 0:
            return False
        if partial.h(sd) == 0:
            return False
        if partial.is_sorted_stack(sd):
            return False
        dest_bad = self._bad_count(partial, sd)
        dest_prefix = partial.sorted_n[sd]
        dest_top = partial.g(sd)
        if dest_bad < self.min_dest_bad_suffix:
            return False
        if dest_prefix < self.min_dest_sorted_prefix or dest_prefix > self.max_dest_sorted_prefix:
            return False
        if self.require_strictly_worse_than_dest_top:
            return moved_group > dest_top
        return moved_group >= dest_top

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved_group = partial.g(so)
        dest_top = partial.g(sd)
        dest_prefix = partial.sorted_n[sd]
        dest_height = partial.h(sd)
        source_height = partial.h(so)
        source_bad = self._bad_count(partial, so)
        dest_bad = self._bad_count(partial, sd)
        parking_gap = moved_group - dest_top
        prefix_rank = dest_prefix if self.prefer_shorter_dest_prefix else -dest_prefix
        dest_height_rank = -dest_height if self.prefer_taller_dest else dest_height
        gap_rank = -parking_gap if self.prefer_larger_parking_gap else parking_gap
        source_height_rank = source_height if self.prefer_shorter_source else -source_height
        return (prefix_rank, dest_height_rank, gap_rank, source_height_rank, -dest_bad, -source_bad, so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if not self._source_ok(partial, so):
                continue
            if not self._dest_ok(partial, sd, partial.g(so)):
                continue
            allowed.append(action)
        if not allowed:
            return []
        return sorted(allowed, key=lambda a: self._sort_key(partial, a))

def build_component(problem, min_source_bad_suffix=2, min_dest_bad_suffix=1, min_dest_sorted_prefix=0, max_dest_sorted_prefix=1, require_nonempty_dest=True, require_strictly_worse_than_dest_top=True, prefer_shorter_dest_prefix=True, prefer_taller_dest=True, prefer_larger_parking_gap=True, prefer_shorter_source=True, **params):
    rule = UnsortedToUnsortedBadSuffixParking(min_source_bad_suffix=min_source_bad_suffix, min_dest_bad_suffix=min_dest_bad_suffix, min_dest_sorted_prefix=min_dest_sorted_prefix, max_dest_sorted_prefix=max_dest_sorted_prefix, require_nonempty_dest=require_nonempty_dest, require_strictly_worse_than_dest_top=require_strictly_worse_than_dest_top, prefer_shorter_dest_prefix=prefer_shorter_dest_prefix, prefer_taller_dest=prefer_taller_dest, prefer_larger_parking_gap=prefer_larger_parking_gap, prefer_shorter_source=prefer_shorter_source)
    return RuleMachine(problem, [rule])
