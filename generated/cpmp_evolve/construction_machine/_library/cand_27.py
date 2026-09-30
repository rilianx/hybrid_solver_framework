from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_to_unsorted_capping_placement', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'require_unsorted_source': {'type': 'bool', 'default': True}, 'min_dest_bad_suffix': {'type': 'int', 'range': [1, 10], 'default': 1}, 'min_source_bad_suffix': {'type': 'int', 'range': [0, 10], 'default': 0}, 'prefer_tighter_cap_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.0}}}

class UnsortedToUnsortedCappingPlacement:
    """Permite mover la cima a un destino desordenado cuando la nueva cima del destino no supera a la actual."""
    name = 'unsorted_to_unsorted_capping_placement'

    def __init__(self, require_unsorted_source: bool, min_dest_bad_suffix: int, min_source_bad_suffix: int, prefer_tighter_cap_weight: float, prefer_shorter_source_weight: float, prefer_more_bad_dest_weight: float, prefer_avoid_singleton_dest: bool):
        self.require_unsorted_source = bool(require_unsorted_source)
        self.min_dest_bad_suffix = int(min_dest_bad_suffix)
        self.min_source_bad_suffix = int(min_source_bad_suffix)
        self.prefer_tighter_cap_weight = float(prefer_tighter_cap_weight)
        self.prefer_shorter_source_weight = float(prefer_shorter_source_weight)
        self.prefer_more_bad_dest_weight = float(prefer_more_bad_dest_weight)
        self.prefer_avoid_singleton_dest = bool(prefer_avoid_singleton_dest)

    def _bad_count(self, partial, stack: int) -> int:
        return partial.h(stack) - partial.sorted_n[stack]

    def _source_ok(self, partial, so: int) -> bool:
        if partial.h(so) == 0:
            return False
        if self.require_unsorted_source and partial.is_sorted_stack(so):
            return False
        return self._bad_count(partial, so) >= self.min_source_bad_suffix

    def _dest_ok(self, partial, so: int, sd: int) -> bool:
        if so == sd or partial.e(sd) <= 0 or partial.h(sd) == 0:
            return False
        if partial.is_sorted_stack(sd):
            return False
        if self._bad_count(partial, sd) < self.min_dest_bad_suffix:
            return False
        return partial.g(sd) >= partial.g(so)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            if not self._source_ok(partial, action.so):
                continue
            if not self._dest_ok(partial, action.so, action.sd):
                continue
            allowed.append(action)
        return allowed

    def score(self, partial, memory, action) -> float:
        so = action.so
        sd = action.sd
        moved = partial.g(so)
        dest_top = partial.g(sd)
        src_h = partial.h(so)
        dst_bad = self._bad_count(partial, sd)
        score = 0.0
        score += self.prefer_tighter_cap_weight * float(dest_top - moved)
        score += self.prefer_shorter_source_weight * float(src_h)
        score -= self.prefer_more_bad_dest_weight * float(dst_bad)
        if self.prefer_avoid_singleton_dest and partial.sorted_n[sd] == 0:
            score += 1.0
        return score

def build_component(problem, require_unsorted_source=True, min_dest_bad_suffix=1, min_source_bad_suffix=0, prefer_tighter_cap_weight=1.0, prefer_shorter_source_weight=0.2, prefer_more_bad_dest_weight=0.5, prefer_avoid_singleton_dest=True):
    rule = UnsortedToUnsortedCappingPlacement(require_unsorted_source=require_unsorted_source, min_dest_bad_suffix=min_dest_bad_suffix, min_source_bad_suffix=min_source_bad_suffix, prefer_tighter_cap_weight=prefer_tighter_cap_weight, prefer_shorter_source_weight=prefer_shorter_source_weight, prefer_more_bad_dest_weight=prefer_more_bad_dest_weight, prefer_avoid_singleton_dest=prefer_avoid_singleton_dest)
    return RuleMachine(problem, [rule])
