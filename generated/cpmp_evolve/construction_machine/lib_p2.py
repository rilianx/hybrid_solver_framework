COMPONENT = {
    "name": "safe_sorted_destination_rule",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from core.rules import RuleMachine


class SafeSortedDestinationRule:
    """Permite solo movimientos hacia una pila no vacía que siga ordenada tras recibir el contenedor."""

    name = "safe_sorted_destination_rule"

    def allowed(self, partial, memory, candidates):
        allowed = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if partial.h(so) <= 0:
                continue
            if partial.h(sd) >= partial.H:
                continue

            src_group = partial.g(so)
            if src_group < 0:
                continue

            # La pila destino debe estar ya ordenada y poder recibir el contenedor
            # sin romper el orden no creciente de abajo hacia arriba.
            if partial.h(sd) == 0:
                continue
            if not partial.is_sorted_stack(sd):
                continue
            if partial.g(sd) >= src_group:
                allowed.append(a)

        return allowed


def build_component(problem, **params):
    return RuleMachine(problem, [SafeSortedDestinationRule()])
