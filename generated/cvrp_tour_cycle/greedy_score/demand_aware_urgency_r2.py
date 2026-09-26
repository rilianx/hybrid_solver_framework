from __future__ import annotations

from math import inf

COMPONENT = {
    "name": "demand_aware_urgency",
    "slot": "greedy_score",
    "compatible_skeletons": [
        "SA",
        "ILS",
        "TS",
        "VNS",
        "GRASP",
        "LNS_MIP",
        "FIX_OPT",
        "LOCAL_BRANCH",
        "MIP_PERTURB",
    ],
    "requires": [],
    "params": {
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "urgency_weight": {"type": "float", "range": [0.0, 10.0]},
        "slack_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class DemandAwareUrgency:
    """CVRP gran tour: puntúa acciones por urgencia de demanda y presión de capacidad.

    Esta versión no replica el criterio puramente incremental de distancia:
    privilegia clientes que consumen capacidad escasa y penaliza decisiones que
    dejan un hueco difícil de reutilizar por el resto de demandas.
    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        distance_weight: float = 0.5,
        urgency_weight: float = 1.0,
        slack_weight: float = 0.2,
    ):
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
                delta = 2.0 * float(self.inst.dist(0, c))
            else:
                last = open_route[-1]
                delta = (
                    float(self.inst.dist(last, c))
                    + float(self.inst.dist(c, 0))
                    - float(self.inst.dist(last, 0))
                )

            # Urgencia por consumo de capacidad: clientes grandes son más prioritarios
            # cuando el hueco disponible es pequeño.
            urgency = d / max(slack + d, 1e-9)

            # Presión de empaquetado: cuántos clientes restantes quedarían con demanda
            # superior al hueco que deja esta elección.
            slack_after = max(0.0, slack - d)
            shortage_count = 0
            for r in remaining:
                if r != c and float(self.inst.demand[r]) > slack_after:
                    shortage_count += 1

            # Además, favorecer demandas grandes si todavía quedan muchos clientes.
            remaining_total_demand = 0.0
            for r in remaining:
                if r != c:
                    remaining_total_demand += float(self.inst.demand[r])
            demand_share = d / max(remaining_total_demand + d, 1e-9)

            return (
                self.distance_weight * delta
                - self.urgency_weight * urgency
                - 0.5 * self.urgency_weight * demand_share
                + self.slack_weight * shortage_count
            )

        if kind == "close":
            # Cerrar es atractivo cuando el hueco actual es poco aprovechable para
            # el conjunto restante; lo contrario desincentiva cerrar demasiado pronto.
            feasible_remaining = 0
            for r in remaining:
                if float(self.inst.demand[r]) <= slack:
                    feasible_remaining += 1

            fill = load / max(cap, 1e-9)
            return self.slack_weight * feasible_remaining - self.urgency_weight * fill

        return inf


def build_component(
    problem,
    distance_weight: float = 0.5,
    urgency_weight: float = 1.0,
    slack_weight: float = 0.2,
):
    return DemandAwareUrgency(
        problem,
        distance_weight=distance_weight,
        urgency_weight=urgency_weight,
        slack_weight=slack_weight,
    )
