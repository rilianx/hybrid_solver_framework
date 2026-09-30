COMPONENT = {'name': 'singleton_sorted_safe_release', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'max_source_height': {'type': 'int', 'range': [1, 3], 'default': 1}, 'min_destination_height': {'type': 'int', 'range': [0, 10], 'default': 1}, 'prefer_tighter_group_fit': {'type': 'bool', 'default': True}}}
from core.rules import RuleMachine

class SingletonSortedSafeRelease:
    """Permite liberar una pila fuente ya ordenada y muy baja moviendo su cima a una pila destino ya ordenada sin desordenarla."""
    name = 'singleton_sorted_safe_release'

    def __init__(self, max_source_height: int, min_destination_height: int, prefer_non_empty_destination: bool, prefer_tighter_group_fit: bool, prefer_taller_sorted_destination: bool):
        self.max_source_height = int(max_source_height)
        self.min_destination_height = int(min_destination_height)
        self.prefer_non_empty_destination = bool(prefer_non_empty_destination)
        self.prefer_tighter_group_fit = bool(prefer_tighter_group_fit)
        self.prefer_taller_sorted_destination = bool(prefer_taller_sorted_destination)

    def _is_eligible_source(self, partial, so: int) -> bool:
        return partial.h(so) > 0 and partial.h(so) <= self.max_source_height and partial.is_sorted_stack(so)

    def _is_safe_sorted_destination(self, partial, so: int, sd: int) -> bool:
        if so == sd or partial.e(sd) <= 0:
            return False
        if partial.h(sd) < self.min_destination_height:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved_group = partial.g(so)
        dest_height = partial.h(sd)
        dest_top = partial.g(sd)
        gap = dest_top - moved_group
        dest_empty = dest_height == 0
        non_empty_rank = dest_empty if self.prefer_non_empty_destination else not dest_empty
        fit_rank = gap if self.prefer_tighter_group_fit else -gap
        height_rank = -dest_height if self.prefer_taller_sorted_destination else dest_height
        return (non_empty_rank, fit_rank, height_rank, so, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            if not self._is_eligible_source(partial, action.so):
                continue
            if not self._is_safe_sorted_destination(partial, action.so, action.sd):
                continue
            allowed.append(action)
        allowed.sort(key=lambda a: self._sort_key(partial, a))
        return allowed

def build_component(problem, max_source_height=1, min_destination_height=1, prefer_non_empty_destination=True, prefer_tighter_group_fit=True, prefer_taller_sorted_destination=True, **params):
    rule = SingletonSortedSafeRelease(max_source_height=max_source_height, min_destination_height=min_destination_height, prefer_non_empty_destination=prefer_non_empty_destination, prefer_tighter_group_fit=prefer_tighter_group_fit, prefer_taller_sorted_destination=prefer_taller_sorted_destination)
    return RuleMachine(problem, [rule])
