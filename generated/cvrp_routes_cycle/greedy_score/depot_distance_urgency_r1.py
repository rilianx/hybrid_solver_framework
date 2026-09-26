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
    """CVRP: estrategia tipo 'farthest-first'.
    Da prioridad a clientes lejanos del depósito para decidir pronto rutas difíciles,
    y usa un pequeño término de balance con la ruta actual para no mezclar clientes
    demasiado incompatibles. Menor puntaje = mejor."""

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

    def _last_customer(self, partial: Any) -> int | None:
        current = getattr(partial, "current", None)
        if current:
            return int(current[-1])
        return None

    def _current_load_ratio(self, partial: Any) -> float:
        current = getattr(partial, "current", None)
        if not current:
            return 0.0
        load = sum(float(self.inst.demand[int(c)]) for c in current)
        cap = float(self.inst.capacity)
        return load / cap if cap > 0 else 0.0

    def score(self, partial: Any, action: Any) -> float:
        c = int(action)
        last = self._last_customer(partial)
        depot_dist = float(self.inst.dist(0, c))

        if last is None:
            return float(-self.far_weight * depot_dist)

        pair = float(self.inst.dist(last, c))
        load_ratio = self._current_load_ratio(partial)

        # Prefer far customers early; once the route is fuller, also favor
        # customers that are not too disruptive relative to the last node.
        return float(
            -self.far_weight * depot_dist
            + self.pair_weight * pair
            + self.balance_weight * abs(0.5 - load_ratio) * depot_dist
        )


def build_component(problem, far_weight: float = 1.0, pair_weight: float = 0.3, balance_weight: float = 0.2):
    return DepotDistanceUrgency(
        problem,
        far_weight=far_weight,
        pair_weight=pair_weight,
        balance_weight=balance_weight,
    )
