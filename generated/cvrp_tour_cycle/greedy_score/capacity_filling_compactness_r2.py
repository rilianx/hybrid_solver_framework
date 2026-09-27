from __future__ import annotations

from math import inf
from generated.cvrp_tour_cycle.model.parts import canonical


COMPONENT = {
    "name": "capacity_filling_compactness",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "fill_weight": {"type": "float", "range": [0.0, 10.0]},
        "compactness_weight": {"type": "float", "range": [0.0, 10.0]},
        "route_restart_penalty": {"type": "float", "range": [0.0, 5.0]},
    },
}


class CapacityFillingCompactness:
    """CVRP gran tour: busca saturar la ruta abierta con clientes que encajen bien.
    Combina uso de capacidad, cercanía mutua al último nodo y compacidad radial
    respecto al depósito. Menor puntaje = mejor."""

    def __init__(
        self,
        problem,
        fill_weight: float = 2.0,
        compactness_weight: float = 0.5,
        route_restart_penalty: float = 0.25,
    ):
        self.inst = problem.inst
        self.fill_weight = fill_weight
        self.compactness_weight = compactness_weight
        self.route_restart_penalty = route_restart_penalty

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "close":
            if not open_route:
                return inf
            load = 0.0
            for c in open_route:
                load += float(self.inst.demand[c])
            cap = max(float(self.inst.capacity), 1e-9)
            fill_ratio = load / cap

            # Preferir cerrar cuando la ruta ya es "larga" espacialmente:
            # una ruta dispersa suele ser mala candidata a seguir creciendo.
            if len(open_route) >= 2:
                min_d = inf
                max_d = 0.0
                for i, a in enumerate(open_route):
                    for b in open_route[i + 1 :]:
                        d = float(self.inst.dist(a, b))
                        if d < min_d:
                            min_d = d
                        if d > max_d:
                            max_d = d
                spread = max_d - min_d
            else:
                spread = 0.0

            return self.route_restart_penalty + (1.0 - fill_ratio) - 0.05 * spread

        c = int(action[1])
        demand_c = float(self.inst.demand[c])
        depot_dist = float(self.inst.dist(0, c))

        if not open_route:
            # Arranque distinto: favorecer clientes que ayuden a "anclar" una ruta
            # espacialmente amplia, no solo los cercanos al último nodo.
            return (
                -self.fill_weight * demand_c
                + self.compactness_weight * depot_dist
                - 0.10 * depot_dist
            )

        # Usamos toda la estructura de la ruta abierta: centroide, dispersión y carga.
        total_x = 0.0
        total_y = 0.0
        for x in open_route:
            px, py = self.inst.xy[x]
            total_x += float(px)
            total_y += float(py)
        n = float(len(open_route))
        cx = total_x / n
        cy = total_y / n

        px, py = self.inst.xy[c]
        to_centroid = ((float(px) - cx) ** 2 + (float(py) - cy) ** 2) ** 0.5

        # Preferimos candidatos que expanden la "envolvente" de la ruta, no los más
        # cercanos al último nodo como en un nearest insertion clásico.
        if len(open_route) >= 2:
            min_d = inf
            max_d = 0.0
            for a in open_route:
                d = float(self.inst.dist(a, c))
                if d < min_d:
                    min_d = d
                if d > max_d:
                    max_d = d
            frontier_gain = max_d - min_d
        else:
            frontier_gain = depot_dist

        load = 0.0
        for x in open_route:
            load += float(self.inst.demand[x])
        remaining_cap = max(float(self.inst.capacity) - load, 0.0)

        # Penaliza "encajar demasiado justo" si no ayuda a expandir la ruta.
        slack = max(0.0, remaining_cap - demand_c)

        return (
            self.fill_weight * slack
            - 0.75 * demand_c
            + self.compactness_weight * to_centroid
            - 0.40 * frontier_gain
            + 0.10 * depot_dist
        )


def build_component(
    problem,
    fill_weight: float = 2.0,
    compactness_weight: float = 0.5,
    route_restart_penalty: float = 0.25,
):
    return CapacityFillingCompactness(
        problem,
        fill_weight=fill_weight,
        compactness_weight=compactness_weight,
        route_restart_penalty=route_restart_penalty,
    )
