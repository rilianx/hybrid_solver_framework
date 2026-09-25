from __future__ import annotations

import math
from typing import Any

from examples.cvrp.problem_model import CVRPInstance, InsertAction, CVRPPartial


COMPONENT = {
    "name": "cheapest_insertion_with_urgency",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "urgency_weight": {"type": "float", "range": [0.0, 5.0]},
        "depot_bias": {"type": "float", "range": [0.0, 5.0]},
    },
}


class CheapestInsertionWithUrgency:
    """CVRP greedy score basado en inserción barata con sesgo por urgencia geométrica.

    Idea:
    - prioriza insertions con bajo incremento de distancia (`action.delta`);
    - favorece atender antes a clientes lejanos del depósito y "difíciles" de encajar
      (lejanos de su entorno local aproximado);
    - penaliza abrir rutas nuevas salvo que el cliente sea realmente urgente.

    Menor puntaje = mejor.
    """

    def __init__(self, problem, urgency_weight: float = 1.5, depot_bias: float = 0.5):
        self.inst: CVRPInstance = problem.inst
        self.urgency_weight = float(urgency_weight)
        self.depot_bias = float(depot_bias)
        n = self.inst.n_customers
        self._depot_dist = [0.0] * (n + 1)
        self._nn_dist = [0.0] * (n + 1)
        for c in self.inst.customers:
            self._depot_dist[c] = self.inst.dist(0, c)
        for c in self.inst.customers:
            best = math.inf
            for d in self.inst.customers:
                if d != c:
                    best = min(best, self.inst.dist(c, d))
            self._nn_dist[c] = 0.0 if best is math.inf else best

    def score(self, partial: CVRPPartial, action: InsertAction) -> float:
        c = action.customer
        urgency = self._depot_dist[c] - self._nn_dist[c]
        # Más urgente => menor puntaje.
        score = action.delta - self.urgency_weight * urgency

        # Sesgo suave contra abrir rutas nuevas, compensado por urgencia.
        if action.new_route:
            score += self.depot_bias * self._depot_dist[c]

        # Inserciones de clientes muy alejados del depósito suelen ser más críticas.
        score += 0.05 * self._depot_dist[c]
        return float(score)


def build_component(problem, urgency_weight: float = 1.5, depot_bias: float = 0.5):
    return CheapestInsertionWithUrgency(problem, urgency_weight=urgency_weight, depot_bias=depot_bias)
