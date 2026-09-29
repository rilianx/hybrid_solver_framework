COMPONENT = {
    "name": "sorted_to_unsorted_bad_suffix_append",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {}
}

from core.rules import RuleMachine


class SortedToUnsortedBadSuffixAppend:
    """Permite mover desde una pila fuente ordenada hacia una pila destino desordenada, apilando sobre su sufijo malo sin empeorar su prefijo bien puesto."""

    name = "sorted_to_unsorted_bad_suffix_append"

    def _is_applicable(self, partial, action):
        so = action.so
        sd = action.sd

        if so == sd:
            return False
        if partial.h(so) == 0:
            return False
        if partial.e(sd) == 0:
            return False

        if not partial.is_sorted_stack(so):
            return False
        if partial.is_sorted_stack(sd):
            return False

        moved = partial.g(so)
        top_dst = partial.g(sd)

        if moved < top_dst:
            return False

        if partial.sorted_n[sd] >= partial.h(sd):
            return False

        return True

    def allowed(self, partial, memory, candidates):
        return [action for action in candidates if self._is_applicable(partial, action)]


def build_component(problem, **params):
    return RuleMachine(problem, [SortedToUnsortedBadSuffixAppend()])
