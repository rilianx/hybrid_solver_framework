COMPONENT = {
    "name": "move_good_top_to_good_stack",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from core.rules import RuleMachine


class MoveGoodTopToGoodStack:
    """Mueve un contenedor tope bien puesto a otra pila no vacía donde también quedará bien puesto."""

    name = "move_good_top_to_good_stack"

    def allowed(self, partial, memory, candidates):
        allowed = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if partial.h(so) == 0 or partial.h(sd) == 0:
                continue
            top = partial.g(so)
            dest_top = partial.g(sd)
            # El origen debe ser un tope bien puesto.
            if not (partial.sorted_n[so] == partial.h(so)):
                continue
            # El movimiento debe mantener el contenedor como bien puesto en el destino.
            if dest_top >= top:
                allowed.append(a)
        return allowed


def build_component(problem, **params):
    return RuleMachine(problem, [MoveGoodTopToGoodStack()])
