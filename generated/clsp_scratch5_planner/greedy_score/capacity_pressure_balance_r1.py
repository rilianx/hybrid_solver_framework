COMPONENT = {
    "name": "capacity_pressure_balance",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "source_pressure_weight": {"type": "float", "range": [0.0, 5.0]},
        "target_pressure_weight": {"type": "float", "range": [0.0, 3.0]},
        "slack_weight": {"type": "float", "range": [0.0, 5.0]},
        "setup_penalty_weight": {"type": "float", "range": [0.0, 5.0]},
        "gap_weight": {"type": "float", "range": [0.0, 2.0]},
    },
}


class CapacityPressureBalance:
    """Puntúa acciones de cobertura priorizando el alivio de presión de capacidad.

    La idea es favorecer fuentes con holgura y penalizar acciones que cargan períodos
    ya tensos, especialmente cuando el `source` queda cerca de su límite.
    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        source_pressure_weight: float = 2.0,
        target_pressure_weight: float = 0.5,
        slack_weight: float = 1.0,
        setup_penalty_weight: float = 1.0,
        gap_weight: float = 0.15,
    ):
        self.inst = problem.inst
        self.source_pressure_weight = source_pressure_weight
        self.target_pressure_weight = target_pressure_weight
        self.slack_weight = slack_weight
        self.setup_penalty_weight = setup_penalty_weight
        self.gap_weight = gap_weight

    def score(self, partial, action):
        inst = self.inst
        s = action.source
        t = action.period

        cap_s = inst.capacity[s]
        cap_t = inst.capacity[t]

        used_s = partial.used[s]
        used_t = partial.used[t]

        add_s = action.qty
        if action.new_setup:
            add_s += inst.setup_time[action.item]

        # Presión actual y futura en la fuente; el núcleo del criterio es evitar
        # saturar períodos ya apretados.
        before_s = used_s / cap_s if cap_s > 0.0 else 0.0
        after_s = (used_s + add_s) / cap_s if cap_s > 0.0 else 0.0
        target_pressure = used_t / cap_t if cap_t > 0.0 else 0.0

        # Holgura remanente en la fuente: cuanto menor, mayor penalización.
        free_after_s = cap_s - used_s - add_s

        # Si la acción incluye nuevo setup, castigar más cuando la fuente está tensa:
        # el setup "se come" capacidad en un período que ya está cerca del límite.
        setup_penalty = 0.0
        if action.new_setup:
            setup_time = inst.setup_time[action.item]
            setup_penalty = self.setup_penalty_weight * (
                (setup_time / cap_s) if cap_s > 0.0 else 0.0
            ) * (1.0 + 2.0 * before_s)

        # Favorecer fuentes tempranas solo en la medida en que estén menos presionadas.
        gap = t - s

        # Criterio principal:
        #  - bajar la presión futura de la fuente
        #  - preferir fuentes más holgadas
        #  - evitar consumir capacidad en períodos congestionados
        score = 0.0
        score += self.source_pressure_weight * after_s
        score += 0.5 * self.source_pressure_weight * before_s
        score += self.target_pressure_weight * target_pressure
        score += self.slack_weight * (1.0 / (1.0 + max(free_after_s, 0.0)))
        score += setup_penalty
        score += self.gap_weight * (gap / max(1, inst.n_periods - 1))

        return float(score)


def build_component(problem, source_pressure_weight: float = 2.0, target_pressure_weight: float = 0.5,
                    slack_weight: float = 1.0, setup_penalty_weight: float = 1.0, gap_weight: float = 0.15):
    return CapacityPressureBalance(
        problem,
        source_pressure_weight=source_pressure_weight,
        target_pressure_weight=target_pressure_weight,
        slack_weight=slack_weight,
        setup_penalty_weight=setup_penalty_weight,
        gap_weight=gap_weight,
    )
