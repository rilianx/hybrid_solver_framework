from core.rules import RuleMachine
COMPONENT = {'name': 'equal_top_frontier_merge', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}

class EqualTopFrontierMerge:
    name = 'equal_top_frontier_merge'

    def __init__(self, require_unsorted_destination=False, prefer_taller_destination=True):
        self.require_unsorted_destination = require_unsorted_destination
        self.prefer_taller_destination = prefer_taller_destination

    def _is_unsorted(self, layout, s):
        h = layout.h(s)
        return h > 0 and layout.sorted_n[s] < h

    def _was_visited(self, partial, so, sd):
        visited = getattr(partial, 'visited', None)
        if visited is None:
            return False
        return partial.after(so, sd) in visited

    def allowed(self, partial, memory, candidates):
        chosen = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if partial.h(so) <= 0:
                continue
            if partial.e(sd) <= 0:
                continue
            if partial.h(sd) <= 0:
                continue
            if partial.g(so) != partial.g(sd):
                continue
            if self.require_unsorted_destination and partial.is_sorted_stack(sd):
                continue
            if self._was_visited(partial, so, sd):
                continue
            src_unsorted = self._is_unsorted(partial, so)
            dst_unsorted = self._is_unsorted(partial, sd)
            if not (src_unsorted or dst_unsorted):
                continue
            chosen.append(a)
        if not chosen:
            return []

        def key(a):
            so = a.so
            sd = a.sd
            src_h = partial.h(so)
            dst_h = partial.h(sd)
            src_unsorted = src_h - partial.sorted_n[so]
            dst_unsorted = dst_h - partial.sorted_n[sd]
            if self.prefer_taller_destination:
                return (-dst_h, -dst_unsorted, src_h, src_unsorted, so, sd)
            return (src_h, src_unsorted, -dst_h, -dst_unsorted, so, sd)
        chosen.sort(key=key)
        return chosen

def build_component(problem, require_unsorted_destination=False, prefer_taller_destination=True, **params):
    rule = EqualTopFrontierMerge(require_unsorted_destination=require_unsorted_destination, prefer_taller_destination=prefer_taller_destination)
    return RuleMachine(problem, [rule])
