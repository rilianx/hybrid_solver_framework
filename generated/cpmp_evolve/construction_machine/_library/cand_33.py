from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_high_blocker_to_bad_suffix_parking', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_bad_suffix': {'type': 'int', 'range': [1, 10], 'default': 2}, 'min_dest_bad_suffix': {'type': 'int', 'range': [1, 10], 'default': 1}, 'min_moved_over_dest_top': {'type': 'int', 'range': [1, 50], 'default': 1}, 'max_dest_sorted_prefix': {'type': 'int', 'range': [0, 10], 'default': 1}, 'prefer_tighter_overshoot': {'type': 'bool', 'default': True}}}

class UnsortedHighBlockerToBadSuffixParking:
    """Permite aparcar un bloqueador alto desde una fuente desordenada sobre un destino ya desordenado y no vacío."""
    name = 'unsorted_high_blocker_to_bad_suffix_parking'

    def __init__(self, min_source_bad_suffix: int, min_dest_bad_suffix: int, min_moved_over_dest_top: int, max_dest_sorted_prefix: int, prefer_shorter_source: bool, prefer_more_disordered_dest: bool, prefer_tighter_overshoot: bool):
        self.min_source_bad_suffix = int(min_source_bad_suffix)
        self.min_dest_bad_suffix = int(min_dest_bad_suffix)
        self.min_moved_over_dest_top = int(min_moved_over_dest_top)
        self.max_dest_sorted_prefix = int(max_dest_sorted_prefix)
        self.prefer_shorter_source = bool(prefer_shorter_source)
        self.prefer_more_disordered_dest = bool(prefer_more_disordered_dest)
        self.prefer_tighter_overshoot = bool(prefer_tighter_overshoot)

    def _bad_count(self, partial, s: int) -> int:
        return partial.h(s) - partial.sorted_n[s]

    def _eligible_source(self, partial, so: int) -> bool:
        return partial.h(so) > 0 and self._bad_count(partial, so) >= self.min_source_bad_suffix

    def _eligible_dest(self, partial, sd: int, moved_group: int) -> bool:
        if partial.e(sd) <= 0 or partial.h(sd) == 0:
            return False
        if partial.is_sorted_stack(sd):
            return False
        if self._bad_count(partial, sd) < self.min_dest_bad_suffix:
            return False
        if partial.sorted_n[sd] > self.max_dest_sorted_prefix:
            return False
        return moved_group >= partial.g(sd) + self.min_moved_over_dest_top

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved_group = partial.g(so)
        dest_top = partial.g(sd)
        overshoot = moved_group - dest_top
        source_height = partial.h(so)
        source_bad = self._bad_count(partial, so)
        dest_bad = self._bad_count(partial, sd)
        dest_prefix = partial.sorted_n[sd]
        source_rank = source_height if self.prefer_shorter_source else -source_height
        dest_bad_rank = -dest_bad if self.prefer_more_disordered_dest else dest_bad
        overshoot_rank = overshoot if self.prefer_tighter_overshoot else -overshoot
        return (dest_prefix, overshoot_rank, source_rank, dest_bad_rank, -source_bad, so, sd)

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
        return sorted(allowed, key=lambda a: self._sort_key(partial, a))

def build_component(problem, min_source_bad_suffix=2, min_dest_bad_suffix=1, min_moved_over_dest_top=1, max_dest_sorted_prefix=1, prefer_shorter_source=True, prefer_more_disordered_dest=True, prefer_tighter_overshoot=True, **params):
    rule = UnsortedHighBlockerToBadSuffixParking(min_source_bad_suffix=min_source_bad_suffix, min_dest_bad_suffix=min_dest_bad_suffix, min_moved_over_dest_top=min_moved_over_dest_top, max_dest_sorted_prefix=max_dest_sorted_prefix, prefer_shorter_source=prefer_shorter_source, prefer_more_disordered_dest=prefer_more_disordered_dest, prefer_tighter_overshoot=prefer_tighter_overshoot)
    return RuleMachine(problem, [rule])
