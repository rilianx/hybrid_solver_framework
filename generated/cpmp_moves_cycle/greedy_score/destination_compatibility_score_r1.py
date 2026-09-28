COMPONENT = {
    "name": "destination_compatibility_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "tightness_weight": {"type": "float", "range": [0.0, 3.0]},
        "support_weight": {"type": "float", "range": [0.0, 3.0]},
    },
}


class DestinationCompatibilityScore:
    """CPMP: prioriza destinos que "soportan" bien al contenedor movido.

    Idea principal:
    - si el tope del destino es cercano en grupo al contenedor movido, el apilado queda más compacto;
    - si el destino ya contiene una secuencia estable, añadir arriba suele ser menos riesgoso.

    Menor puntaje = mejor acción.
    """

    def __init__(self, problem, tightness_weight: float = 1.0, support_weight: float = 0.75):
        self.inst = problem.inst
        self.tightness_weight = float(tightness_weight)
        self.support_weight = float(support_weight)

    @staticmethod
    def _ordered_suffix_length(stack: tuple[int, ...]) -> int:
        if len(stack) <= 1:
            return len(stack)
        k = len(stack)
        while k > 1 and stack[k - 2] >= stack[k - 1]:
            k -= 1
        return len(stack) - (k - 1)

    def score(self, partial, action) -> float:
        state = partial.state
        so, sd = int(action[0]), int(action[1])

        src = state[so]
        dst = state[sd]
        moving = src[-1]

        # Compatibilidad con el tope del destino.
        if dst:
            top = dst[-1]
            tightness = abs(top - moving)
            support = 1.0 if top >= moving else 2.0  # poner un contenedor más "difícil" encima suele empeorar.
        else:
            tightness = 0.5  # pila vacía: neutral, pero no tan buena como una buena compatibilidad.
            support = 1.0

        # Si el destino ya tiene un sufijo ordenado largo, añadir arriba es más natural.
        ordered_suffix = self._ordered_suffix_length(dst)
        suffix_bonus = 1.0 / (1.0 + ordered_suffix)

        # Penaliza usar destinos demasiado llenos.
        fill = len(dst) / max(self.inst.H, 1)

        return (
            self.tightness_weight * tightness
            + self.support_weight * support
            + 0.5 * suffix_bonus
            + 0.25 * fill
        )


def build_component(problem, tightness_weight: float = 1.0, support_weight: float = 0.75):
    return DestinationCompatibilityScore(problem, tightness_weight=tightness_weight, support_weight=support_weight)
