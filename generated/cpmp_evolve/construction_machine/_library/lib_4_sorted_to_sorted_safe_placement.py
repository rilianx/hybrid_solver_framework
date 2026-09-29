COMPONENT = {'name': 'sorted_to_sorted_safe_placement', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from core.rules import RuleMachine

class SortedToSortedSafePlacementRule:
    """Permite mover la cima de una pila fuente ordenada a una pila destino ordenada si el destino sigue ordenado."""
    name = 'sorted_to_sorted_safe_placement'

    def __init__(self, require_source_remains_sorted=True):
        self.require_source_remains_sorted = require_source_remains_sorted

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if so == sd:
                continue
            if partial.h(so) == 0:
                continue
            if partial.e(sd) == 0:
                continue
            if not partial.is_sorted_stack(so):
                continue
            if not partial.is_sorted_stack(sd):
                continue
            moved_group = partial.g(so)
            destination_top = partial.g(sd)
            if destination_top < moved_group:
                continue
            if self.require_source_remains_sorted:
                next_layout_hash = partial.after(so, sd)
                if partial.visited is not None and next_layout_hash in partial.visited:
                    continue
            allowed.append(action)
        return allowed

def build_component(problem, **params):
    rule = SortedToSortedSafePlacementRule(require_source_remains_sorted=params.get('require_source_remains_sorted', True))
    return RuleMachine(problem, [rule])
