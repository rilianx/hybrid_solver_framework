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
    """CVRP: estrategia de urgencia por capacidad y cierre de ruta.

    A diferencia de un criterio puramente de cercanía, prioriza clientes que:
    - tienen mayor demanda relativa a la capacidad restante de la ruta actual,
    - son más lejanos del depósito, para resolverlos antes,
    - y, en menor medida, son compatibles con el último cliente de la ruta.

    Menor puntaje = mejor."""

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

    def _last_customer(self, partial: Any) -> int | None:
        current = self._current_route(partial)
        return current[-1] if current else None

    def _remaining_capacity_ratio(self, partial: Any, action_customer: int) -> float:
        current = self._current_route(partial)
        load = sum(float(self.inst.demand[int(c)]) for c in current) + float(self.inst.demand[action_customer])
        cap = float(self.inst.capacity)
        if cap <= 0.0:
            return 0.0
        remaining = max(0.0, cap - load)
        return remaining / cap

    def score(self, partial: Any, action: Any) -> float:
        c = int(action)
        depot_dist = float(self.inst.dist(0, c))
        demand = float(self.inst.demand[c])

        # Un cliente ya "urgente" si consume mucha capacidad; esto empuja
        # a tratar antes a los clientes grandes, incluso si no son los más cercanos.
        cap = float(self.inst.capacity)
        demand_ratio = (demand / cap) if cap > 0.0 else demand

        last = self._last_customer(partial)
        if last is None:
            # En el arranque, el criterio se apoya sobre todo en urgencia y distancia al depósito.
            return float(-self.far_weight * depot_dist - self.balance_weight * demand_ratio)

        pair = float(self.inst.dist(last, c))
        remaining_ratio = self._remaining_capacity_ratio(partial, c)

        # Penaliza menos a clientes "difíciles" que fuerzan a cerrar una ruta pronto.
        # El término de balance favorece consumir capacidad de forma más decidida,
        # evitando dejar grandes demandas para el final.
        return float(
            -self.far_weight * depot_dist
            - self.balance_weight * demand_ratio
            + self.pair_weight * pair
            + self.balance_weight * remaining_ratio * demand_ratio
        )


def build_component(problem, far_weight: float = 1.0, pair_weight: float = 0.3, balance_weight: float = 0.2):
    return DepotDistanceUrgency(
        problem,
        far_weight=far_weight,
        pair_weight=pair_weight,
        balance_weight=balance_weight,
    )
