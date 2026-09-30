COMPONENT = {'name': 'unsorted_to_sorted_safe_placement_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'prioritize_tighter_group_fit': {'type': 'bool', 'default': True}}}
from core.rules import RuleMachine

class UnsortedToSortedSafePlacementRefined:
    """Permite mover la cima de una pila fuente desordenada a una pila destino ordenada si el destino sigue ordenado, priorizando cierres limpios de la fuente."""
    name = 'unsorted_to_sorted_safe_placement'

    def __init__(self, prefer_non_empty_destination: bool=True, prioritize_source_becomes_sorted: bool=True, prioritize_tighter_group_fit: bool=True, prefer_taller_destination: bool=True, filter_visited: bool=True):
        self.prefer_non_empty_destination = prefer_non_empty_destination
        self.prioritize_source_becomes_sorted = prioritize_source_becomes_sorted
        self.prioritize_tighter_group_fit = prioritize_tighter_group_fit
        self.prefer_taller_destination = prefer_taller_destination
        self.filter_visited = filter_visited

    def _is_unsorted_source(self, partial, so):
        return partial.h(so) > 0 and (not partial.is_sorted_stack(so))

    def _keeps_destination_sorted(self, partial, so, sd):
        if partial.h(so) == 0 or partial.h(sd) >= partial.H:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _would_repeat(self, partial, so, sd):
        return self.filter_visited and partial.visited is not None and (partial.after(so, sd) in partial.visited)

    def _source_becomes_sorted(self, partial, so):
        return partial.sorted_n[so] == partial.h(so) - 1

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            if not self._is_unsorted_source(partial, action.so):
                continue
            if not self._keeps_destination_sorted(partial, action.so, action.sd):
                continue
            if self._would_repeat(partial, action.so, action.sd):
                continue
            allowed.append(action)

        def key(action):
            so = action.so
            sd = action.sd
            dest_empty = partial.h(sd) == 0
            gap = partial.g(sd) - partial.g(so)
            source_finishes = self._source_becomes_sorted(partial, so)
            parts = []
            if self.prioritize_source_becomes_sorted:
                parts.append(not source_finishes)
            if self.prefer_non_empty_destination:
                parts.append(dest_empty)
            if self.prioritize_tighter_group_fit:
                parts.append(gap)
            if self.prefer_taller_destination:
                parts.append(-partial.h(sd))
            else:
                parts.append(partial.h(sd))
            parts.extend([-partial.sorted_n[sd], partial.h(so) - partial.sorted_n[so], so, sd])
            return tuple(parts)
        allowed.sort(key=key)
        return allowed

def build_component(problem, **params):
    rule = UnsortedToSortedSafePlacementRefined(prefer_non_empty_destination=params.get('prefer_non_empty_destination', True), prioritize_source_becomes_sorted=params.get('prioritize_source_becomes_sorted', True), prioritize_tighter_group_fit=params.get('prioritize_tighter_group_fit', True), prefer_taller_destination=params.get('prefer_taller_destination', True), filter_visited=params.get('filter_visited', True))
    return RuleMachine(problem, [rule])
