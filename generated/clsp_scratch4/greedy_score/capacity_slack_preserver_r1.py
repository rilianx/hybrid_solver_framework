from __future__ import annotations

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "capacity_slack_preserver",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "slack_weight": {"type": "float", "range": [0.0, 10.0]},
        "setup_pressure_weight": {"type": "float", "range": [0.0, 10.0]},
        "deadline_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class CapacitySlackPreserver:
    """Favorece acciones que consumen menos capacidad escasa y preservan holgura.

    Idea distinta:
    - no mira tanto el costo del ítem, sino la presión sobre la capacidad del período source,
    - prefiere usar fuentes con mucha holgura,
    - penaliza encender nuevos setups cuando el source está congestionado,
    - da prioridad a cubrir deadlines cercanos.

    Menor score = mejor.
    """

    def __init__(
        self,
        problem,
        slack_weight: float = 1.0,
        setup_pressure_weight: float = 1.0,
        deadline_weight: float = 1.0,
    ):
        self.inst: CLSPInstance = problem.inst
        self.slack_weight = float(slack_weight)
        self.setup_pressure_weight = float(setup_pressure_weight)
        self.deadline_weight = float(deadline_weight)

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i = action.item
        t = action.period
        s = action.source
        q = max(action.qty, 1e-12)

        free_s = max(partial.free(s), 0.0)
        cap_s = max(inst.capacity[s], 1e-12)
        setup_time = inst.setup_time[i] if action.new_setup else 0.0

        # Congestión relativa del source: cuanto más lleno, peor.
        pressure = (partial.used[s] + setup_time) / cap_s

        # Cubrir pronto es mejor; periodos más tardíos reciben menos prioridad.
        deadline = 1.0 / (1.0 + t)

        # Preferir acciones que dejan más capacidad libre en el source.
        slack = 1.0 / (1.0 + free_s)

        # Penalizar lotes diminutos cuando implican encender setup.
        tiny_batch = (inst.setup_cost[i] / q) if action.new_setup else 0.0

        return (
            self.slack_weight * slack
            + self.setup_pressure_weight * pressure
            + self.deadline_weight * deadline
            + 0.001 * tiny_batch
        )


def build_component(problem, slack_weight: float = 1.0, setup_pressure_weight: float = 1.0, deadline_weight: float = 1.0):
    return CapacitySlackPreserver(
        problem,
        slack_weight=slack_weight,
        setup_pressure_weight=setup_pressure_weight,
        deadline_weight=deadline_weight,
    )
