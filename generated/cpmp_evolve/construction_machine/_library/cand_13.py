COMPONENT = {'name': 'unsorted_to_sorted_safe_placement_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'max_gap': {'type': 'int', 'range': [0, 99], 'default': 99}, 'min_destination_sorted_prefix': {'type': 'int', 'range': [0, 99], 'default': 1}}}
from core.rules import RuleMachine

class UnsortedToSortedSafePlacementRefined:
    """Permite mover desde una fuente desordenada a un destino ordenado que sigue ordenado, reordenando por cierre limpio y encaje seguro."""
    name = 'unsorted_to_sorted_safe_placement'

    def __init__(self, prefer_non_empty_destination: bool=True, prefer_source_closure: bool=True, max_gap: int=99, min_destination_sorted_prefix: int=1):
        self.prefer_non_empty_destination = prefer_non_empty_destination
        self.prefer_source_closure = prefer_source_closure
        self.max_gap = max_gap
        self.min_destination_sorted_prefix = min_destination_sorted_prefix

    def _keeps_destination_sorted(self, partial, so, sd):
        if partial.h(so) == 0 or partial.h(sd) >= partial.H:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _is_unsorted_source(self, partial, so):
        return partial.h(so) > 0 and (not partial.is_sorted_stack(so))

    def _closes_source_cleanly(self, partial, so):
        return partial.h(so) > 0 and partial.sorted_n[so] == partial.h(so) - 1

    def _eligible(self, partial, action):
        if not self._is_unsorted_source(partial, action.so):
            return False
        if not self._keeps_destination_sorted(partial, action.so, action.sd):
            return False
        gap = partial.g(action.sd) - partial.g(action.so)
        if gap > self.max_gap:
            return False
        if partial.sorted_n[action.sd] < self.min_destination_sorted_prefix:
            return False
        return True

    def allowed(self, partial, memory, candidates):
        allowed = [a for a in candidates if self._eligible(partial, a)]

        def key(action):
            gap = partial.g(action.sd) - partial.g(action.so)
            dest_empty = partial.h(action.sd) == 0
            closes_source = self._closes_source_cleanly(partial, action.so)
            if self.prefer_non_empty_destination and self.prefer_source_closure:
                return (not closes_source, dest_empty, gap, -partial.sorted_n[action.sd], -partial.h(action.sd), partial.h(action.so), action.so, action.sd)
            if self.prefer_source_closure:
                return (not closes_source, gap, dest_empty, -partial.sorted_n[action.sd], -partial.h(action.sd), partial.h(action.so), action.so, action.sd)
            if self.prefer_non_empty_destination:
                return (dest_empty, gap, -partial.sorted_n[action.sd], -partial.h(action.sd), partial.h(action.so), action.so, action.sd)
            return (gap, dest_empty, -partial.sorted_n[action.sd], -partial.h(action.sd), partial.h(action.so), action.so, action.sd)
        allowed.sort(key=key)
        return allowed

def build_component(problem, **params):
    rule = UnsortedToSortedSafePlacementRefined(prefer_non_empty_destination=params.get('prefer_non_empty_destination', True), prefer_source_closure=params.get('prefer_source_closure', True), max_gap=params.get('max_gap', 99), min_destination_sorted_prefix=params.get('min_destination_sorted_prefix', 1))
    return RuleMachine(problem, [rule])
