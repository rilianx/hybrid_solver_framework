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
    """CVRP gran tour: puntúa acciones por presión de capacidad y urgencia de demanda.

    Idea distinta a un criterio puramente incremental de distancia:
    se centra en cómo cada decisión afecta al "encaje" de las demandas restantes
    respecto a la capacidad de la ruta abierta y al número mínimo de rutas aún
    necesarias. Menor puntaje = mejor.
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
        load = 0.0
        for c in open_route:
            load += float(self.inst.demand[c])
        slack = max(0.0, cap - load)

        remaining_total_demand = 0.0
        for r in remaining:
            remaining_total_demand += float(self.inst.demand[r])

        if kind == "add":
            c = int(action[1])
            d = float(self.inst.demand[c])

            # Costo geométrico solo como desempate suave: no domina la decisión.
            if not open_route:
                delta = 2.0 * float(self.inst.dist(0, c))
            else:
                last = open_route[-1]
                delta = (
                    float(self.inst.dist(last, c))
                    + float(self.inst.dist(c, 0))
                    - float(self.inst.dist(last, 0))
                )

            # Cuánta capacidad consume el cliente respecto al hueco disponible.
            # Si el hueco es pequeño y el cliente es grande, la acción es urgente.
            fill_ratio = d / max(slack + d, 1e-9)

            # Objetivo de llenado: aproximar el uso de capacidad al promedio que
            # exigirían las demandas restantes repartidas entre las rutas mínimas.
            routes_lb = 1.0
            if remaining_total_demand > 0.0:
                routes_lb = max(1.0, remaining_total_demand / max(cap, 1e-9))
            target_load = min(cap, remaining_total_demand / routes_lb if routes_lb > 0 else cap)
            balance_penalty = abs((load + d) - target_load) / max(cap, 1e-9)

            # Si tras añadir c queda un slack pequeño, penaliza los clientes restantes
            # que ya no cabrían en esa ruta: esto guía a cerrar solo cuando conviene.
            slack_after = max(0.0, slack - d)
            stranded = 0
            for r in remaining:
                if r != c and float(self.inst.demand[r]) > slack_after:
                    stranded += 1

            # Preferir demandas grandes cuando el conjunto restante aún es amplio.
            demand_share = d / max(remaining_total_demand, 1e-9)

            return (
                self.distance_weight * delta
                - self.urgency_weight * fill_ratio
                - 0.75 * self.urgency_weight * demand_share
                + self.slack_weight * balance_penalty
                + 0.25 * self.slack_weight * stranded
            )

        if kind == "close":
            # Cerrar es mejor cuando la ruta abierta ya está "bien llena" y,
            # al mismo tiempo, el remanente sigue teniendo mucha demanda agregada.
            fill = load / max(cap, 1e-9)

            feasible_remaining = 0
            min_rem_demand = None
            max_rem_demand = 0.0
            for r in remaining:
                dr = float(self.inst.demand[r])
                if dr <= slack:
                    feasible_remaining += 1
                if min_rem_demand is None or dr < min_rem_demand:
                    min_rem_demand = dr
                if dr > max_rem_demand:
                    max_rem_demand = dr

            # Si el hueco actual es raro de reutilizar, cerrar se vuelve atractivo.
            rarity = 0.0
            if min_rem_demand is not None:
                rarity = max(0.0, min_rem_demand - slack) / max(cap, 1e-9)

            # Penaliza cerrar si todavía caben muchos restantes en la ruta abierta.
            return (
                self.slack_weight * feasible_remaining
                + self.slack_weight * rarity
                - self.urgency_weight * fill
                + 0.1 * self.urgency_weight * (remaining_total_demand / max(cap, 1e-9))
            )

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
