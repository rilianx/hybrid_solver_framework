from core.rules import RuleMachine
COMPONENT = {'name': 'sorted_source_consolidation_v2', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_height': {'type': 'int', 'range': [1, 10], 'default': 1}, 'max_source_height': {'type': 'int', 'range': [1, 10], 'default': 3}, 'max_bad_suffix': {'type': 'int', 'range': [0, 3], 'default': 1}, 'min_sorted_prefix': {'type': 'int', 'range': [0, 10], 'default': 1}, 'allow_empty_destination': {'type': 'bool', 'default': False}, 'require_destination_sorted': {'type': 'bool', 'default': True}, 'prefer_free_source': {'type': 'bool', 'default': True}, 'prefer_safe_destination': {'type': 'bool', 'default': True}, 'tight_fit_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.2}}}

class RefinedSortedSourceConsolidation:
    """Consolida desde fuentes ordenadas o casi ordenadas bajas hacia destinos seguros, priorizando liberar la fuente."""
    name = 'sorted_source_consolidation'

    def __init__(self, min_source_height, max_source_height, max_bad_suffix, min_sorted_prefix, allow_empty_destination, require_destination_sorted, prefer_free_source, prefer_safe_destination, prefer_sorted_source, prefer_non_empty_destination, tight_fit_weight, destination_height_weight):
        self.min_source_height = int(min_source_height)
        self.max_source_height = int(max_source_height)
        self.max_bad_suffix = int(max_bad_suffix)
        self.min_sorted_prefix = int(min_sorted_prefix)
        self.allow_empty_destination = bool(allow_empty_destination)
        self.require_destination_sorted = bool(require_destination_sorted)
        self.prefer_free_source = bool(prefer_free_source)
        self.prefer_safe_destination = bool(prefer_safe_destination)
        self.prefer_sorted_source = bool(prefer_sorted_source)
        self.prefer_non_empty_destination = bool(prefer_non_empty_destination)
        self.tight_fit_weight = float(tight_fit_weight)
        self.destination_height_weight = float(destination_height_weight)

    def _bad_suffix(self, partial, stack):
        return partial.h(stack) - partial.sorted_n[stack]

    def _is_sorted_source(self, partial, stack):
        return partial.h(stack) > 0 and partial.is_sorted_stack(stack)

    def _is_near_sorted_source(self, partial, stack):
        h = partial.h(stack)
        if h == 0:
            return False
        bad = self._bad_suffix(partial, stack)
        return bad > 0 and bad <= self.max_bad_suffix and (partial.sorted_n[stack] >= self.min_sorted_prefix)

    def _source_ok(self, partial, stack):
        h = partial.h(stack)
        if h < self.min_source_height or h > self.max_source_height:
            return False
        return self._is_sorted_source(partial, stack) or self._is_near_sorted_source(partial, stack)

    def _destination_ok(self, partial, so, sd):
        if so == sd or partial.e(sd) <= 0:
            return False
        if partial.h(sd) == 0:
            return self.allow_empty_destination
        if self.require_destination_sorted and (not partial.is_sorted_stack(sd)):
            return False
        return True

    def _is_safe_destination(self, partial, so, sd):
        if partial.h(sd) == 0:
            return True
        return partial.is_sorted_stack(sd) and partial.g(sd) >= partial.g(so)

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

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        src_h = partial.h(so)
        dst_h = partial.h(sd)
        moved = partial.g(so)
        dst_top = partial.g(sd)
        src_sorted = self._is_sorted_source(partial, so)
        safe_dst = self._is_safe_destination(partial, so, sd)
        frees_source = src_h == 1
        non_empty_dst = dst_h > 0
        gap = 0 if dst_h == 0 else abs(dst_top - moved)
        free_rank = 0 if self.prefer_free_source and frees_source else 1 if self.prefer_free_source else 0
        safe_rank = 0 if self.prefer_safe_destination and safe_dst else 1 if self.prefer_safe_destination else 0
        sorted_rank = 0 if self.prefer_sorted_source and src_sorted else 1 if self.prefer_sorted_source else 0
        non_empty_rank = 0 if self.prefer_non_empty_destination and non_empty_dst else 1 if self.prefer_non_empty_destination else 0
        weighted_gap = self.tight_fit_weight * float(gap)
        weighted_dest_height = -self.destination_height_weight * float(dst_h)
        return (free_rank, safe_rank, sorted_rank, non_empty_rank, weighted_gap, weighted_dest_height, src_h, so, sd)

def build_component(problem, min_source_height=1, max_source_height=3, max_bad_suffix=1, min_sorted_prefix=1, allow_empty_destination=False, require_destination_sorted=True, prefer_free_source=True, prefer_safe_destination=True, prefer_sorted_source=True, prefer_non_empty_destination=True, tight_fit_weight=0.2, destination_height_weight=0.5):
    rule = RefinedSortedSourceConsolidation(min_source_height=min_source_height, max_source_height=max_source_height, max_bad_suffix=max_bad_suffix, min_sorted_prefix=min_sorted_prefix, allow_empty_destination=allow_empty_destination, require_destination_sorted=require_destination_sorted, prefer_free_source=prefer_free_source, prefer_safe_destination=prefer_safe_destination, prefer_sorted_source=prefer_sorted_source, prefer_non_empty_destination=prefer_non_empty_destination, tight_fit_weight=tight_fit_weight, destination_height_weight=destination_height_weight)
    return RuleMachine(problem, [rule])
