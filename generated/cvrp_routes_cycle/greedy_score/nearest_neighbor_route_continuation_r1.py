from __future__ import annotations

from typing import Any

COMPONENT = {
    "name": "nearest_neighbor_route_continuation",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "current_weight": {"type": "float", "range": [0.0, 10.0]},
        "depot_weight": {"type": "float", "range": [0.0, 10.0]},
        "lookahead_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class NearestNeighborRouteContinuation:
    """CVRP: puntúa cada cliente por su conveniencia para continuar la ruta abierta.
    Menor puntaje = mejor. Favorece clientes cercanos al último de la ruta actual,
    y en menor medida clientes que también quedan cerca del depósito, para evitar
    rutas con retorno costoso."""

    def __init__(
        self,
        problem,
        current_weight: float = 1.0,
        depot_weight: float = 0.2,
        lookahead_weight: float = 0.1,
    ):
        self.inst = problem.inst
        self.current_weight = float(current_weight)
        self.depot_weight = float(depot_weight)
        self.lookahead_weight = float(lookahead_weight)

    def _current_last(self, partial: Any) -> int | None:
        current = getattr(partial, "current", None)
        if current:
            return int(current[-1])
        return None

    def score(self, partial: Any, action: Any) -> float:
        c = int(action)
        last = self._current_last(partial)

        if last is None:
            base = self.inst.dist(0, c)
            return float(base + self.depot_weight * self.inst.dist(c, 0))

        d_last = self.inst.dist(last, c)
        d_depot = self.inst.dist(c, 0)
        return float(
            self.current_weight * d_last
            + self.depot_weight * d_depot
            + self.lookahead_weight * (self.inst.dist(0, c) + self.inst.dist(last, 0)) * 0.5
        )


def build_component(problem, current_weight: float = 1.0, depot_weight: float = 0.2, lookahead_weight: float = 0.1):
    return NearestNeighborRouteContinuation(
        problem,
        current_weight=current_weight,
        depot_weight=depot_weight,
        lookahead_weight=lookahead_weight,
    )
