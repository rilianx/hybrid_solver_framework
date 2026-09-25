from __future__ import annotations

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "capacity_balancing_pressure",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "scarcity_weight": {"type": "float", "range": [0.0, 5.0]},
        "source_slack_weight": {"type": "float", "range": [0.0, 5.0]},
        "item_load_weight": {"type": "float", "range": [0.0, 5.0]},
        "setup_penalty_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class CapacityBalancingPressure:
    """Favorece acciones que usan fuentes con más holgura y evitan congestionar períodos escasos.

    Menor puntaje = mejor. La idea es:
    - despriorizar acciones desde períodos con poca capacidad libre;
    - favorecer ítems cuyas demandas futuras todavía son pesadas, para no dejar una carga concentrada;
    - penalizar nuevos setups en períodos congestionados;
    - usar la holgura del período fuente como señal de balanceo.
    """

    def __init__(
        self,
        problem,
        scarcity_weight: float = 1.0,
        source_slack_weight: float = 1.0,
        item_load_weight: float = 1.0,
        setup_penalty_weight: float = 1.0,
    ):
        self.inst: CLSPInstance = problem.inst
        self.scarcity_weight = scarcity_weight
        self.source_slack_weight = source_slack_weight
        self.item_load_weight = item_load_weight
        self.setup_penalty_weight = setup_penalty_weight

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i = action.item
        t = action.period
        s = action.source

        free_source = partial.free(s)
        free_deadline = partial.free(t)
        pending_item = sum(partial.rem[i][tt] for tt in range(t, inst.n_periods))

        # Periodos más escasos deben reservarse: cuanto menos libre, peor.
        scarcity_term = self.scarcity_weight * (1.0 / (1.0 + max(free_source, 0.0)))

        # Preferir usar fuentes más holgadas.
        slack_term = -self.source_slack_weight * max(free_source, 0.0)

        # Ítems con mucha carga pendiente merecen atención temprana.
        load_term = -self.item_load_weight * float(pending_item)

        # Penalizar abrir setups nuevos, especialmente si el deadline ya está muy apretado.
        setup_term = self.setup_penalty_weight * (1.0 if action.new_setup else 0.0) * (1.0 / (1.0 + max(free_deadline, 0.0)))

        # Sesgo pequeño hacia fuentes cercanas al deadline.
        proximity_term = 1e-6 * float(t - s)

        return scarcity_term + slack_term + load_term + setup_term + proximity_term


def build_component(problem, scarcity_weight: float = 1.0, source_slack_weight: float = 1.0,
                    item_load_weight: float = 1.0, setup_penalty_weight: float = 1.0):
    return CapacityBalancingPressure(
        problem,
        scarcity_weight=scarcity_weight,
        source_slack_weight=source_slack_weight,
        item_load_weight=item_load_weight,
        setup_penalty_weight=setup_penalty_weight,
    )
