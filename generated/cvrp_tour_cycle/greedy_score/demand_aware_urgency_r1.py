from __future__ import annotations

from math import inf

COMPONENT = {
    "name": "demand_aware_urgency",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "urgency_weight": {"type": "float", "range": [0.0, 10.0]},
        "slack_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class DemandAwareUrgency:
    """CVRP gran tour: prioriza clientes 'urgentes' por demanda y por la presión de capacidad.
    La idea es consumir antes los clientes que más restringen el empaquetado futuro.
    Menor puntaje = mejor."""

    def __init__(self, problem, distance_weight: float = 0.5, urgency_weight: float = 1.0, slack_weight: float = 0.2):
        self.inst = problem.inst
        self.distance_weight = float(distance_weight)
        self.urgency_weight = float(urgency_weight)
        self.slack_weight = float(slack_weight)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        cap = float(self.inst.capacity)
        load = sum(self.inst.demand[c] for c in open_route)
        slack = max(0.0, cap - load)

        if kind == "add":
            c = int(action[1])
            d = float(self.inst.demand[c])

            if not open_route:
                delta = 2.0 * self.inst.dist(0, c)
            else:
                last = open_route[-1]
                delta = self.inst.dist(last, c) + self.inst.dist(c, 0) - self.inst.dist(last, 0)

            # Urgency: larger demand becomes more attractive when slack is limited.
            urgency = d / max(slack + d, 1e-9)
            # Also favor large customers when many remain, to reduce risk of fragmentation.
            remaining_pressure = d / max(sum(self.inst.demand[r] for r in remaining), 1e-9)
            return self.distance_weight * delta - self.urgency_weight * urgency - 0.5 * self.urgency_weight * remaining_pressure

        if kind == "close":
            # Prefer closing when the current route is relatively full; otherwise keep it open.
            fill = load / max(cap, 1e-9)
            return self.slack_weight * (1.0 - fill)

        return inf


def build_component(problem, distance_weight: float = 0.5, urgency_weight: float = 1.0, slack_weight: float = 0.2):
    return DemandAwareUrgency(
        problem,
        distance_weight=distance_weight,
        urgency_weight=urgency_weight,
        slack_weight=slack_weight,
    )
