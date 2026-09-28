from __future__ import annotations

from math import inf

COMPONENT = {
    "name": "route_utilization_balance",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "utilization_weight": {"type": "float", "range": [0.0, 10.0]},
        "open_route_penalty": {"type": "float", "range": [0.0, 10.0]},
    },
}


class RouteUtilizationBalance:
    """CVRP gran tour: prioriza cortes que produzcan rutas con carga razonablemente
    equilibrada respecto a la demanda restante. La idea principal no es minimizar
    distancia incremental, sino favorecer rutas cuyo nivel de carga quede cerca
    de una utilización alta y homogénea."""

    def __init__(
        self,
        problem,
        distance_weight: float = 1.0,
        utilization_weight: float = 1.0,
        open_route_penalty: float = 0.3,
    ):
        self.inst = problem.inst
        self.distance_weight = float(distance_weight)
        self.utilization_weight = float(utilization_weight)
        self.open_route_penalty = float(open_route_penalty)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]
        cap = float(self.inst.capacity)
        cap_inv = 1.0 / max(cap, 1e-9)

        load = 0.0
        for c in open_route:
            load += float(self.inst.demand[c])

        remaining_demand = 0.0
        remaining_count = 0
        for c in remaining:
            remaining_demand += float(self.inst.demand[c])
            remaining_count += 1

        if kind == "add":
            c = int(action[1])
            d = float(self.inst.demand[c])
            new_load = load + d
            slack = max(cap - new_load, 0.0)

            # Principal criterio: dejar la ruta abierta tan cerca de la capacidad
            # como sea posible, evitando tanto rutas flojas como cierres excesivos.
            fill_gap = slack * cap_inv
            utilization_term = fill_gap * fill_gap

            # Sesgo estructural: si queda mucha demanda por delante, conviene incorporar
            # clientes que ayuden a cerrar rutas "densas" en vez de dejar cargas dispersas.
            avg_remaining = remaining_demand / max(1.0, float(remaining_count))
            balance_term = abs(new_load - min(cap, avg_remaining * max(1.0, float(len(open_route) + 1)))) * cap_inv

            # Preferencia suave por comenzar/continuar rutas con clientes de demanda útil.
            # Esto empuja a formar rutas más compactas en carga, no necesariamente en distancia.
            demand_term = max(0.0, (cap - d) * cap_inv)

            return (
                self.utilization_weight * utilization_term
                + self.distance_weight * balance_term
                + self.open_route_penalty * demand_term
            )

        if kind == "close":
            # Cerrar es bueno si la carga ya está cerca de la capacidad.
            fill_gap = max(cap - load, 0.0) * cap_inv
            utilization_term = fill_gap * fill_gap

            # Penaliza cierres demasiado tempranos cuando todavía queda mucha demanda
            # y la ruta actual está lejos de una "porción" natural del problema.
            avg_remaining = remaining_demand / max(1.0, float(remaining_count)) if remaining_count else 0.0
            balance_term = abs(load - min(cap, avg_remaining * max(1.0, float(len(open_route))))) * cap_inv

            # Si la ruta está vacía o casi vacía, cerrar es muy malo; si está razonablemente llena,
            # la penalización cae rápido.
            emptiness_term = 1.0 / max(1.0, float(len(open_route)))

            return (
                self.open_route_penalty * utilization_term
                + self.distance_weight * balance_term
                + self.utilization_weight * emptiness_term
            )

        return inf


def build_component(
    problem,
    distance_weight: float = 1.0,
    utilization_weight: float = 1.0,
    open_route_penalty: float = 0.3,
):
    return RouteUtilizationBalance(
        problem,
        distance_weight=distance_weight,
        utilization_weight=utilization_weight,
        open_route_penalty=open_route_penalty,
    )
