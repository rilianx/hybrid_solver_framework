from __future__ import annotations

from typing import Any

COMPONENT = {
    "name": "capacity_fill_and_route_break_penalty",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "fill_weight": {"type": "float", "range": [0.0, 10.0]},
        "break_weight": {"type": "float", "range": [0.0, 20.0]},
        "demand_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class CapacityFillAndRouteBreakPenalty:
    """CVRP: puntúa acciones por cómo llenan la capacidad de la ruta abierta.
    Prefiere completar bien la capacidad sin excederla y penaliza dejar una ruta
    "casi vacía" cuando una acción provocaría cerrar la ruta actual. Menor puntaje = mejor."""

    def __init__(
        self,
        problem,
        fill_weight: float = 1.0,
        break_weight: float = 2.0,
        demand_weight: float = 0.3,
    ):
        self.inst = problem.inst
        self.fill_weight = float(fill_weight)
        self.break_weight = float(break_weight)
        self.demand_weight = float(demand_weight)

    def _current_load(self, partial: Any) -> float:
        current = getattr(partial, "current", None)
        if not current:
            return 0.0
        return float(sum(self.inst.demand[int(c)] for c in current))

    def score(self, partial: Any, action: Any) -> float:
        c = int(action)
        d = float(self.inst.demand[c])
        current = getattr(partial, "current", None)
        load = self._current_load(partial)
        cap = float(self.inst.capacity)

        if not current:
            slack = cap - d
            fill = slack / cap if cap > 0 else 0.0
            return float(self.fill_weight * fill - self.demand_weight * d)

        if load + d <= cap:
            slack = cap - (load + d)
            fill = slack / cap if cap > 0 else 0.0
            return float(self.fill_weight * fill - self.demand_weight * d)

        overflow = (load + d) - cap
        # If the action forces a route break, prefer customers whose demand helps
        # close the current route tightly and whose own demand is larger.
        break_penalty = overflow / cap if cap > 0 else overflow
        return float(self.break_weight * break_penalty - self.demand_weight * d)


def build_component(problem, fill_weight: float = 1.0, break_weight: float = 2.0, demand_weight: float = 0.3):
    return CapacityFillAndRouteBreakPenalty(
        problem,
        fill_weight=fill_weight,
        break_weight=break_weight,
        demand_weight=demand_weight,
    )
