from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_to_unsorted_capping_placement', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_dest_sorted_prefix': {'type': 'int', 'range': [0, 10], 'default': 1}, 'max_source_bad_suffix': {'type': 'int', 'range': [1, 10], 'default': 10}, 'prefer_tighter_cap': {'type': 'bool', 'default': True}}}

class UnsortedToUnsortedCappingPlacement:
    """Permite tapar el tope de una pila destino desordenada con la cima de una fuente desordenada, dejando ordenado el nuevo par superior."""
    name = 'unsorted_to_unsorted_capping_placement'

    def __init__(self, min_dest_sorted_prefix: int, max_source_bad_suffix: int, require_nonempty_dest: bool, prefer_longer_dest_prefix: bool, prefer_tighter_cap: bool, prefer_shorter_source: bool):
        self.min_dest_sorted_prefix = int(min_dest_sorted_prefix)
        self.max_source_bad_suffix = int(max_source_bad_suffix)
        self.require_nonempty_dest = bool(require_nonempty_dest)
        self.prefer_longer_dest_prefix = bool(prefer_longer_dest_prefix)
        self.prefer_tighter_cap = bool(prefer_tighter_cap)
        self.prefer_shorter_source = bool(prefer_shorter_source)

    def _bad_count(self, partial, s):
        return partial.h(s) - partial.sorted_n[s]

    def _is_unsorted_source(self, partial, s):
        return partial.h(s) > 0 and (not partial.is_sorted_stack(s)) and (self._bad_count(partial, s) >= 1) and (self._bad_count(partial, s) <= self.max_source_bad_suffix)

    def _is_cappable_unsorted_dest(self, partial, s):
        if partial.e(s) <= 0:
            return False
        if self.require_nonempty_dest and partial.h(s) == 0:
            return False
        return partial.h(s) > 0 and (not partial.is_sorted_stack(s)) and (partial.sorted_n[s] >= self.min_dest_sorted_prefix)

    def _caps_destination_top(self, partial, so, sd):
        return partial.g(sd) >= partial.g(so)

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved = partial.g(so)
        dest_top = partial.g(sd)
        gap = dest_top - moved
        dest_prefix = partial.sorted_n[sd]
        src_height = partial.h(so)
        src_bad = self._bad_count(partial, so)
        dest_height = partial.h(sd)
        k1 = -dest_prefix if self.prefer_longer_dest_prefix else dest_prefix
        k2 = gap if self.prefer_tighter_cap else -gap
        k3 = src_height if self.prefer_shorter_source else -src_height
        return (k1, k2, k3, src_bad, -dest_height, so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if so == sd:
                continue
            if not self._is_unsorted_source(partial, so):
                continue
            if not self._is_cappable_unsorted_dest(partial, sd):
                continue
            if not self._caps_destination_top(partial, so, sd):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self._sort_key(partial, a))
        return allowed

def build_component(problem, min_dest_sorted_prefix=1, max_source_bad_suffix=10, require_nonempty_dest=True, prefer_longer_dest_prefix=True, prefer_tighter_cap=True, prefer_shorter_source=True, **params):
    rule = UnsortedToUnsortedCappingPlacement(min_dest_sorted_prefix=min_dest_sorted_prefix, max_source_bad_suffix=max_source_bad_suffix, require_nonempty_dest=require_nonempty_dest, prefer_longer_dest_prefix=prefer_longer_dest_prefix, prefer_tighter_cap=prefer_tighter_cap, prefer_shorter_source=prefer_shorter_source)
    return RuleMachine(problem, [rule])
