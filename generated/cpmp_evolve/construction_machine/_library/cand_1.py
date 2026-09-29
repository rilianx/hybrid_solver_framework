COMPONENT = {
    "name": "move_to_empty_stack_rule",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {
        "only_when_multiple_empties": {"type": "bool", "default": False},
    },
}

from core.rules import RuleMachine


class MoveToEmptyStackRule:
    """Permite solo movimientos cuyo destino es una pila vacía."""

    name = "move_to_empty_stack_rule"

    def __init__(self, only_when_multiple_empties=False):
        self.only_when_multiple_empties = bool(only_when_multiple_empties)

    @staticmethod
    def _get_height(partial, idx):
        if hasattr(partial, "h"):
            return partial.h(idx)
        stacks = getattr(partial, "stacks", None)
        return len(stacks[idx]) if stacks is not None else 0

    @staticmethod
    def _get_empty_count(partial):
        stacks = getattr(partial, "stacks", None)
        if stacks is not None:
            return sum(1 for s in stacks if len(s) == 0)
        if hasattr(partial, "S"):
            return sum(1 for i in range(partial.S) if partial.h(i) == 0)
        return 0

    def allowed(self, partial, memory, candidates):
        empty_count = self._get_empty_count(partial)
        if self.only_when_multiple_empties and empty_count < 2:
            return []

        allowed = []
        for a in candidates:
            sd = getattr(a, "sd", None)
            if sd is None:
                continue
            if self._get_height(partial, sd) == 0:
                allowed.append(a)
        return allowed


def build_component(problem, **params):
    rule = MoveToEmptyStackRule(
        only_when_multiple_empties=params.get(
            "only_when_multiple_empties",
            COMPONENT["params"]["only_when_multiple_empties"]["default"],
        )
    )
    return RuleMachine(problem, [rule])
