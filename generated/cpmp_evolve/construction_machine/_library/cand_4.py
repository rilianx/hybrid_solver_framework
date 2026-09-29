COMPONENT = {
    "name": "move_good_top_to_bad_stack",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {
        "prefer_more_bad_destinations": {
            "type": "bool",
            "default": True,
        }
    },
}

from core.rules import RuleMachine


class MoveGoodTopToBadStack:
    """Mueve un tope bien puesto a una pila donde quedará mal puesto."""

    name = "move_good_top_to_bad_stack"

    def __init__(self, prefer_more_bad_destinations: bool = True):
        self.prefer_more_bad_destinations = prefer_more_bad_destinations

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []

        allowed = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if partial.h(so) <= 0 or partial.h(sd) >= partial.H:
                continue

            moved = partial.g(so)
            if moved is None:
                continue

            # Fuente: el tope debe estar bien puesto.
            # Para una pila no vacía, el tope es bien puesto si su posición está
            # dentro del prefijo ordenado desde abajo.
            if partial.h(so) > partial.sorted_n[so]:
                continue

            # Destino: el contenedor debe quedar mal puesto al aterrizar.
            dest_top = partial.g(sd)
            if dest_top is None:
                # En una pila vacía el contenedor queda bien puesto; no aplica.
                continue
            if dest_top >= moved:
                continue

            allowed.append(a)

        if not allowed:
            return []

        if self.prefer_more_bad_destinations:
            # Prioriza destinos donde el nuevo tope quede "más mal" respecto al tope actual.
            allowed.sort(key=lambda a: (partial.g(a.sd) - partial.g(a.so), a.so, a.sd))
        return allowed


def build_component(problem, **params):
    prefer_more_bad_destinations = params.get("prefer_more_bad_destinations", True)
    return RuleMachine(problem, [MoveGoodTopToBadStack(prefer_more_bad_destinations=prefer_more_bad_destinations)])
