COMPONENT = {'name': 'unsorted_to_sorted_safe_placement', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from core.rules import RuleMachine

class UnsortedToSortedSafePlacement:
    """Permite mover la cima de una pila fuente desordenada a una pila destino ordenada si el destino sigue ordenado."""
    name = 'unsorted_to_sorted_safe_placement'

    def __init__(self, prefer_non_empty_destination: bool=True):
        self.prefer_non_empty_destination = prefer_non_empty_destination

    def _keeps_destination_sorted(self, partial, so, sd):
        if partial.h(so) == 0 or partial.h(sd) >= partial.H:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _is_unsorted_source(self, partial, so):
        return partial.h(so) > 0 and (not partial.is_sorted_stack(so))

    def allowed(self, partial, memory, candidates):
        allowed = [action for action in candidates if self._is_unsorted_source(partial, action.so) and self._keeps_destination_sorted(partial, action.so, action.sd)]

        def key(action):
            gap = partial.g(action.sd) - partial.g(action.so)
            dest_empty = partial.h(action.sd) == 0
            if self.prefer_non_empty_destination:
                return (dest_empty, gap, -partial.sorted_n[action.sd], -partial.h(action.sd), action.so, action.sd)
            return (gap, dest_empty, -partial.sorted_n[action.sd], -partial.h(action.sd), action.so, action.sd)
        allowed.sort(key=key)
        return allowed

def build_component(problem, **params):
    rule = UnsortedToSortedSafePlacement(prefer_non_empty_destination=params.get('prefer_non_empty_destination', True))
    return RuleMachine(problem, [rule])
