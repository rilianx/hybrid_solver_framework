COMPONENT = {
    "name": "dump_to_deepest_nonempty_stack_rule",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from core.rules import RuleMachine


class DumpToDeepestNonEmptyStackRule:
    """Permite solo movimientos a una pila no vacía con máxima holgura (más huecos)."""

    name = "dump_to_deepest_nonempty_stack_rule"

    def allowed(self, partial, memory, candidates):
        non_empty = []
        for a in candidates:
            if partial.h(a.sd) > 0:
                non_empty.append(a)
        if not non_empty:
            return []

        best_free = max(partial.e(a.sd) for a in non_empty)
        return [a for a in non_empty if partial.e(a.sd) == best_free]


def build_component(problem, **params):
    return RuleMachine(problem, [DumpToDeepestNonEmptyStackRule()])
