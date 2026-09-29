COMPONENT = {
    "name": "move_good_top_to_empty_stack",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from core.rules import RuleMachine


class MoveGoodTopToEmptyStack:
    """Mueve un tope bien puesto a una pila vacía."""

    name = "move_good_top_to_empty_stack"

    def allowed(self, partial, memory, candidates):
        out = []
        stacks = partial.stacks
        heights = partial.H
        for a in candidates:
            so = a.so
            sd = a.sd
            if not stacks[so]:
                continue
            if len(stacks[sd]) != 0:
                continue
            top = stacks[so][-1]
            if len(stacks[so]) == 1:
                top_good = True
            else:
                top_good = top <= stacks[so][-2]
            if top_good:
                out.append(a)
        return out


def build_component(problem, **params):
    return RuleMachine(problem, [MoveGoodTopToEmptyStack()])
