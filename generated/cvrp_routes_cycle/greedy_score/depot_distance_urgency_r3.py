from __future__ import annotations

from typing import Any

COMPONENT = {
    "name": "depot_distance_urgency",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "far_weight": {"type": "float", "range": [0.0, 10.0]},
        "pair_weight": {"type": "float", "range": [0.0, 10.0]},
        "balance_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class DepotDistanceUrgency:
    """CVRP: puntuación greedy por urgencia de carga y cierre de ruta.

    La idea no es continuar la ruta por cercanía al último cliente, sino
    priorizar clientes que:
    - consumen una fracción importante de la capacidad disponible,
    - están lejos del depósito, para resolver antes los más costosos,
    - y dejan menos holgura residual al cerrar la ruta.

    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        far_weight: float = 1.0,
        pair_weight: float = 0.3,
        balance_weight: float = 0.2,
    ):
        self.inst = problem.inst
        self.far_weight = float(far_weight)
        self.pair_weight = float(pair_weight)
        self.balance_weight = float(balance_weight)

    def _current_route(self, partial: Any) -> list[int]:
        current = getattr(partial, "current", None)
        if not current:
            return []
        return [int(c) for c in current]

    def _route_load(self, partial: Any) -> float:
        current = self._current_route(partial)
        return sum(float(self.inst.demand[int(c)]) for c in current)

    def score(self, partial: Any, action: Any) -> float:
        c = int(action)
        cap = float(self.inst.capacity)
        demand = float(self.inst.demand[c])
        depot_dist = float(self.inst.dist(0, c))

        current_load = self._route_load(partial)
        if cap > 0.0:
            demand_ratio = demand / cap
            residual_after = max(0.0, cap - (current_load + demand)) / cap
        else:
            demand_ratio = demand
            residual_after = 0.0

        # En vez de depender del último cliente (criterio de continuación),
        # puntuamos por "urgencia de llenado": clientes grandes y lejanos
        # al depósito se vuelven preferentes, y además buscamos dejar poca
        # holgura residual en la ruta actual.
        return float(
            -self.far_weight * depot_dist
            - self.balance_weight * demand_ratio
            + self.pair_weight * residual_after
            + self.balance_weight * residual_after * demand_ratio
        )


def build_component(problem, far_weight: float = 1.0, pair_weight: float = 0.3, balance_weight: float = 0.2):
    return DepotDistanceUrgency(
        problem,
        far_weight=far_weight,
        pair_weight=pair_weight,
        balance_weight=balance_weight,
    )
