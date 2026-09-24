from __future__ import annotations

from typing import Protocol

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "capacity_congestion_aware",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "congestion_weight": {"type": "float", "range": [0.0, 20.0]},
        "setup_time_weight": {"type": "float", "range": [0.0, 20.0]},
        "load_balance_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class CapacityCongestionAware:
    """Puntúa según congestión de la capacidad en el período fuente.

    Idea:
    - si el período fuente ya está cargado, evitar añadir más presión allí;
    - castigar setups con mucho tiempo de preparación en períodos apretados;
    - favorecer acciones que ayuden a balancear carga entre períodos.
    Distinto enfoque: mira la holgura local de capacidad, no solo costo/urgencia.
    """

    def __init__(
        self,
        problem,
        congestion_weight: float = 2.0,
        setup_time_weight: float = 1.0,
        load_balance_weight: float = 0.5,
    ):
        self.inst: CLSPInstance = problem.inst
        self.congestion_weight = congestion_weight
        self.setup_time_weight = setup_time_weight
        self.load_balance_weight = load_balance_weight

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i, s, q = action.item, action.source, action.qty

        cap = max(inst.capacity[s], 1e-9)
        used_ratio = partial.used[s] / cap
        free_after = partial.free(s) - (inst.setup_time[i] if action.new_setup else 0.0) - q

        # Congestión local: más caro usar períodos ya cargados.
        congestion = used_ratio

        # Penaliza setups con tiempos grandes, sobre todo si el período está congestionado.
        setup_time_term = inst.setup_time[i] if action.new_setup else 0.0

        # Balanceo: preferir acciones que no dejen el período excesivamente apretado.
        balance_term = 0.0 if free_after >= 0 else 1e6

        # Un pequeño ajuste por cantidad: lotes muy pequeños son menos atractivos si no alivian carga.
        quantity_term = 1.0 / max(q, 1e-9)

        return (
            self.congestion_weight * congestion
            + self.setup_time_weight * setup_time_term / cap
            + self.load_balance_weight * quantity_term
            + balance_term
        )


def build_component(problem, congestion_weight: float = 2.0, setup_time_weight: float = 1.0, load_balance_weight: float = 0.5):
    return CapacityCongestionAware(
        problem,
        congestion_weight=congestion_weight,
        setup_time_weight=setup_time_weight,
        load_balance_weight=load_balance_weight,
    )
