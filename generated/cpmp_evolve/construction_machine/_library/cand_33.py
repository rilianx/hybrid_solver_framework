COMPONENT = {'name': 'unsorted_to_unsorted_suffix_cap_extension', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_dest_bad_suffix': {'type': 'int', 'range': [1, 6], 'default': 1}, 'min_dest_top_run': {'type': 'int', 'range': [1, 6], 'default': 1}, 'min_source_bad_count': {'type': 'int', 'range': [1, 6], 'default': 1}, 'prefer_longer_dest_top_run': {'type': 'bool', 'default': True}, 'prefer_tighter_fit': {'type': 'bool', 'default': True}}}
from core.rules import RuleMachine

class UnsortedToUnsortedSuffixCapExtension:
    """Permite mover la cima de una fuente desordenada a un destino desordenado no vacío si extiende el sufijo superior no creciente del destino."""
    name = 'unsorted_to_unsorted_suffix_cap_extension'

    def __init__(self, min_dest_bad_suffix: int, min_dest_top_run: int, min_source_bad_count: int, prefer_expose_sorted_source: bool, prefer_longer_dest_top_run: bool, prefer_tighter_fit: bool):
        self.min_dest_bad_suffix = int(min_dest_bad_suffix)
        self.min_dest_top_run = int(min_dest_top_run)
        self.min_source_bad_count = int(min_source_bad_count)
        self.prefer_expose_sorted_source = bool(prefer_expose_sorted_source)
        self.prefer_longer_dest_top_run = bool(prefer_longer_dest_top_run)
        self.prefer_tighter_fit = bool(prefer_tighter_fit)

    def _bad_count(self, partial, s):
        return partial.h(s) - partial.sorted_n[s]

    def _top_nonincreasing_run_len(self, partial, s):
        h = partial.h(s)
        if h <= 0:
            return 0
        stk = partial.stacks[s]
        run = 1
        i = h - 1
        while i > 0 and stk[i - 1] >= stk[i]:
            run += 1
            i -= 1
        return run

    def _dest_bad_suffix_len(self, partial, s):
        return partial.h(s) - partial.sorted_n[s]

    def _source_ok(self, partial, s):
        return partial.h(s) > 0 and (not partial.is_sorted_stack(s)) and (self._bad_count(partial, s) >= self.min_source_bad_count)

    def _dest_ok(self, partial, so, sd):
        if so == sd or partial.e(sd) <= 0 or partial.h(sd) <= 0:
            return False
        if partial.is_sorted_stack(sd):
            return False
        moved = partial.g(so)
        top = partial.g(sd)
        if moved > top:
            return False
        if self._dest_bad_suffix_len(partial, sd) < self.min_dest_bad_suffix:
            return False
        if self._top_nonincreasing_run_len(partial, sd) < self.min_dest_top_run:
            return False
        return True

    def _exposes_sorted_source(self, partial, so):
        return self._bad_count(partial, so) == 1

    def _key(self, partial, action):
        so = action.so
        sd = action.sd
        moved = partial.g(so)
        top = partial.g(sd)
        dest_run = self._top_nonincreasing_run_len(partial, sd)
        gap = top - moved
        expose_rank = 0 if self.prefer_expose_sorted_source and self._exposes_sorted_source(partial, so) else 1
        if not self.prefer_expose_sorted_source:
            expose_rank = 0
        run_rank = -dest_run if self.prefer_longer_dest_top_run else dest_run
        gap_rank = gap if self.prefer_tighter_fit else -gap
        return (expose_rank, run_rank, gap_rank, partial.h(so), -partial.h(sd), so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            if not self._source_ok(partial, action.so):
                continue
            if not self._dest_ok(partial, action.so, action.sd):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self._key(partial, a))
        return allowed

def build_component(problem, min_dest_bad_suffix=1, min_dest_top_run=1, min_source_bad_count=1, prefer_expose_sorted_source=True, prefer_longer_dest_top_run=True, prefer_tighter_fit=True, **params):
    rule = UnsortedToUnsortedSuffixCapExtension(min_dest_bad_suffix=min_dest_bad_suffix, min_dest_top_run=min_dest_top_run, min_source_bad_count=min_source_bad_count, prefer_expose_sorted_source=prefer_expose_sorted_source, prefer_longer_dest_top_run=prefer_longer_dest_top_run, prefer_tighter_fit=prefer_tighter_fit)
    return RuleMachine(problem, [rule])
