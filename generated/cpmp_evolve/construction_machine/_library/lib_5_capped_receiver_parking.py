COMPONENT = {'name': 'capped_receiver_parking', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from core.rules import RuleMachine

class CappedReceiverParkingRule:
    """Permite crear o seguir una pila receptora 'tapada': base ordenada + sufijo superior de aparcamiento."""
    name = 'capped_receiver_parking'

    def __init__(self, prefer_existing_cap=True, prefer_tighter_start_fit=True):
        self.prefer_existing_cap = prefer_existing_cap
        self.prefer_tighter_start_fit = prefer_tighter_start_fit

    def _source_resolves_after_pop(self, partial, so):
        h = partial.h(so)
        return h > 0 and partial.sorted_n[so] >= h - 1

    def _suffix_is_nondecreasing_down_to_up(self, stack, start):
        if start >= len(stack):
            return False
        idx = start + 1
        while idx < len(stack):
            if stack[idx - 1] < stack[idx]:
                return False
            idx += 1
        return True

    def _is_capped_receiver(self, partial, sd):
        h = partial.h(sd)
        k = partial.sorted_n[sd]
        if h <= 0 or k <= 0 or k >= h:
            return False
        return self._suffix_is_nondecreasing_down_to_up(partial.stacks[sd], k)

    def _is_start_of_cap(self, partial, so, sd):
        if so == sd or partial.e(sd) <= 0:
            return False
        if not self._source_resolves_after_pop(partial, so):
            return False
        if not partial.is_sorted_stack(sd):
            return False
        x = partial.g(so)
        y = partial.g(sd)
        return x > y

    def _is_continue_cap(self, partial, so, sd):
        if so == sd or partial.e(sd) <= 0:
            return False
        if not self._source_resolves_after_pop(partial, so):
            return False
        if not self._is_capped_receiver(partial, sd):
            return False
        x = partial.g(so)
        y = partial.g(sd)
        return x <= y

    def allowed(self, partial, memory, candidates):
        starts = []
        conts = []
        for a in candidates:
            if self._is_continue_cap(partial, a.so, a.sd):
                conts.append(a)
            elif self._is_start_of_cap(partial, a.so, a.sd):
                starts.append(a)
        if self.prefer_tighter_start_fit:
            starts.sort(key=lambda a: partial.g(a.so) - partial.g(a.sd))
        else:
            starts.sort(key=lambda a: (a.sd, a.so))
        conts.sort(key=lambda a: (-partial.sorted_n[a.sd], partial.g(a.sd) - partial.g(a.so), a.sd, a.so))
        if self.prefer_existing_cap and conts:
            return conts + starts
        return starts + conts

    def score(self, partial, memory, action):
        if self._is_continue_cap(partial, action.so, action.sd):
            return 0.0
        return float(partial.g(action.so) - partial.g(action.sd))

def build_component(problem, **params):
    rule = CappedReceiverParkingRule(prefer_existing_cap=params.get('prefer_existing_cap', True), prefer_tighter_start_fit=params.get('prefer_tighter_start_fit', True))
    return RuleMachine(problem, [rule])
