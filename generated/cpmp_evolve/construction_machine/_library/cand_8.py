COMPONENT = {
    "name": "move_bad_top_to_empty_stack",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {}
}

from core.rules import RuleMachine


class MoveBadTopToEmptyStack:
    """Mueve un contenedor tope mal puesto a una pila vacía."""

    name = "move_bad_top_to_empty_stack"

    def allowed(self, partial, memory, candidates):
        out = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if partial.h(so) == 0:
                continue
            if partial.h(sd) != 0:
                continue
            # tope mal puesto en origen
            if partial.h(so) <= partial.sorted_n[so]:
                continue
            out.append(a)
        return out


def build_component(problem, **params):
    return RuleMachine(problem, [MoveBadTopToEmptyStack()])
