COMPONENT = {'name': 'sorted_source_consolidation', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_source_height': {'type': 'int', 'range': [1, 10], 'default': 1}, 'max_source_height': {'type': 'int', 'range': [1, 10], 'default': 3}, 'max_bad_suffix': {'type': 'int', 'range': [0, 2], 'default': 1}, 'min_sorted_prefix': {'type': 'int', 'range': [0, 10], 'default': 1}, 'prefer_free_source': {'type': 'bool', 'default': True}}}
from core.rules import RuleMachine

class StrictSortedSourceConsolidation:
    """Consolida desde fuentes bajas ordenadas o casi ordenadas hacia destinos ordenados manteniendo el destino ordenado."""
    name = 'sorted_source_consolidation'

    def __init__(self, min_source_height: int, max_source_height: int, max_bad_suffix: int, min_sorted_prefix: int, require_progress: bool, prefer_free_source: bool, prefer_exact_fit: bool, prefer_taller_sorted_dest: bool):
        self.min_source_height = int(min_source_height)
        self.max_source_height = int(max_source_height)
        self.max_bad_suffix = int(max_bad_suffix)
        self.min_sorted_prefix = int(min_sorted_prefix)
        self.require_progress = bool(require_progress)
        self.prefer_free_source = bool(prefer_free_source)
        self.prefer_exact_fit = bool(prefer_exact_fit)
        self.prefer_taller_sorted_dest = bool(prefer_taller_sorted_dest)

    def _source_data(self, partial, s):
        h = partial.h(s)
        sorted_n = partial.sorted_n[s]
        bad_suffix = h - sorted_n
        is_sorted = partial.is_sorted_stack(s)
        is_near_sorted = h > 0 and bad_suffix > 0 and (bad_suffix <= self.max_bad_suffix) and (sorted_n >= self.min_sorted_prefix)
        return (h, sorted_n, bad_suffix, is_sorted, is_near_sorted)

    def _eligible_source(self, partial, s):
        h, sorted_n, bad_suffix, is_sorted, is_near_sorted = self._source_data(partial, s)
        if h < self.min_source_height or h > self.max_source_height:
            return False
        if sorted_n < self.min_sorted_prefix:
            return False
        if is_sorted:
            return True
        return is_near_sorted and bad_suffix <= self.max_bad_suffix

    def _safe_sorted_destination(self, partial, so, sd):
        if so == sd:
            return False
        if partial.e(sd) <= 0:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _makes_progress(self, partial, so):
        h, sorted_n, bad_suffix, is_sorted, is_near_sorted = self._source_data(partial, so)
        if h == 1:
            return True
        if is_sorted:
            return True
        if is_near_sorted and bad_suffix >= 1:
            return True
        return False

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        src_h, src_sorted, src_bad, src_is_sorted, src_is_near_sorted = self._source_data(partial, so)
        moved = partial.g(so)
        dst_h = partial.h(sd)
        dst_top = partial.g(sd)
        frees_source = src_h == 1
        peels_last_bad = src_bad == 1 and src_is_near_sorted
        exact_fit = dst_top == moved
        gap = dst_top - moved
        free_rank = not frees_source if self.prefer_free_source else frees_source
        exact_fit_rank = not exact_fit if self.prefer_exact_fit else exact_fit
        taller_dest_rank = -dst_h if self.prefer_taller_sorted_dest else dst_h
        return (free_rank, not peels_last_bad, not src_is_sorted, exact_fit_rank, gap, taller_dest_rank, src_h, so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if not self._eligible_source(partial, so):
                continue
            if not self._safe_sorted_destination(partial, so, sd):
                continue
            if self.require_progress and (not self._makes_progress(partial, so)):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self._sort_key(partial, a))
        return allowed

def build_component(problem, min_source_height=1, max_source_height=3, max_bad_suffix=1, min_sorted_prefix=1, require_progress=True, prefer_free_source=True, prefer_exact_fit=True, prefer_taller_sorted_dest=True):
    rule = StrictSortedSourceConsolidation(min_source_height=min_source_height, max_source_height=max_source_height, max_bad_suffix=max_bad_suffix, min_sorted_prefix=min_sorted_prefix, require_progress=require_progress, prefer_free_source=prefer_free_source, prefer_exact_fit=prefer_exact_fit, prefer_taller_sorted_dest=prefer_taller_sorted_dest)
    return RuleMachine(problem, [rule])
