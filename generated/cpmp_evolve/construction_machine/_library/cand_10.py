from dataclasses import dataclass
from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_to_sorted_safe_placement_targeted', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}

@dataclass(frozen=True)
class _RuleMemory:
    target_source: int | None

class UnsortedToSortedSafePlacement:
    """Mueve desde una fuente desordenada hacia un destino ordenado que permanece ordenado."""
    name = 'unsorted_to_sorted_safe_placement'

    def __init__(self, prefer_non_empty_destination: bool=True, prefer_exact_fit: bool=True, focus_single_source: bool=True, source_choice: str='fewest_destinations_most_sorted'):
        self.prefer_non_empty_destination = prefer_non_empty_destination
        self.prefer_exact_fit = prefer_exact_fit
        self.focus_single_source = focus_single_source
        self.source_choice = source_choice

    def _is_unsorted_source(self, partial, so):
        return partial.h(so) > 0 and (not partial.is_sorted_stack(so))

    def _keeps_destination_sorted(self, partial, so, sd):
        if so == sd:
            return False
        if partial.h(so) == 0 or partial.h(sd) >= partial.H:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        return partial.g(sd) >= partial.g(so)

    def _sorted_destinations(self, partial, so):
        return [sd for sd in range(partial.S) if self._keeps_destination_sorted(partial, so, sd)]

    def _source_rank(self, partial, so):
        destinations = self._sorted_destinations(partial, so)
        dest_count = len(destinations)
        sorted_prefix = partial.sorted_n[so]
        unsorted_suffix = partial.h(so) - sorted_prefix
        top_group = partial.g(so)
        if self.source_choice == 'most_sorted_fewest_destinations':
            return (-sorted_prefix, dest_count, unsorted_suffix, -top_group, so)
        return (dest_count, -sorted_prefix, unsorted_suffix, -top_group, so)

    def _pick_source(self, partial):
        feasible_sources = [so for so in range(partial.S) if self._is_unsorted_source(partial, so) and self._sorted_destinations(partial, so)]
        if not feasible_sources:
            return None
        feasible_sources.sort(key=lambda so: self._source_rank(partial, so))
        return feasible_sources[0]

    def start(self, partial, memory):
        return _RuleMemory(target_source=self._pick_source(partial))

    def done(self, partial, memory):
        if not self.focus_single_source:
            return True
        if not isinstance(memory, _RuleMemory):
            return True
        target_source = memory.target_source
        if target_source is None:
            return True
        if not self._is_unsorted_source(partial, target_source):
            return True
        return not self._sorted_destinations(partial, target_source)

    def _action_key(self, partial, action):
        gap = partial.g(action.sd) - partial.g(action.so)
        is_exact_fit = gap == 0
        dest_empty = partial.h(action.sd) == 0
        source_rank = self._source_rank(partial, action.so)
        exact_fit_rank = 0 if self.prefer_exact_fit and is_exact_fit else 1
        non_empty_rank = 0 if self.prefer_non_empty_destination and (not dest_empty) else 1
        return (source_rank, exact_fit_rank, non_empty_rank, gap, -partial.sorted_n[action.sd], -partial.h(action.sd), action.so, action.sd)

    def allowed(self, partial, memory, candidates):
        target_source = None
        if self.focus_single_source and isinstance(memory, _RuleMemory):
            target_source = memory.target_source
        allowed = []
        for action in candidates:
            if not self._is_unsorted_source(partial, action.so):
                continue
            if target_source is not None and action.so != target_source:
                continue
            if self._keeps_destination_sorted(partial, action.so, action.sd):
                allowed.append(action)
        if not allowed and self.focus_single_source and (target_source is not None):
            for action in candidates:
                if not self._is_unsorted_source(partial, action.so):
                    continue
                if self._keeps_destination_sorted(partial, action.so, action.sd):
                    allowed.append(action)
        allowed.sort(key=lambda action: self._action_key(partial, action))
        return allowed

def build_component(problem, **params):
    rule = UnsortedToSortedSafePlacement(prefer_non_empty_destination=params.get('prefer_non_empty_destination', True), prefer_exact_fit=params.get('prefer_exact_fit', True), focus_single_source=params.get('focus_single_source', True), source_choice=params.get('source_choice', 'fewest_destinations_most_sorted'))
    return RuleMachine(problem, [rule])
