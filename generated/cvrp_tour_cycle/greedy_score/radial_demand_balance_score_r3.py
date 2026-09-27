from __future__ import annotations

from math import inf
from generated.cvrp_tour_cycle.model.parts import canonical


COMPONENT = {
    "name": "radial_demand_balance_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "radial_weight": {"type": "float", "range": [0.0, 10.0]},
        "balance_weight": {"type": "float", "range": [0.0, 10.0]},
        "close_empty_penalty": {"type": "float", "range": [0.0, 10.0]},
    },
}


class RadialDemandBalanceScore:
    """CVRP gran tour: favorece clientes que están radialmente cerca del depósito
    pero también "equilibran" la carga. La idea es construir rutas con clientes
    relativamente próximos al depot y con demanda que use bien la capacidad.
    Menor puntaje = mejor."""

    def __init__(
        self,
        problem,
        radial_weight: float = 1.0,
        balance_weight: float = 1.0,
        close_empty_penalty: float = 3.0,
    ):
        self.inst = problem.inst
        self.radial_weight = radial_weight
        self.balance_weight = balance_weight
        self.close_empty_penalty = close_empty_penalty

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        cap = max(float(self.inst.capacity), 1e-9)

        if kind == "close":
            if not open_route:
                return inf
            load = 0.0
            for c in open_route:
                load += float(self.inst.demand[c])

            unused = max(cap - load, 0.0) / cap
            # Cerrar una ruta es más atractivo cuando quedan clientes muy "lejanos"
            # que conviene dejar para una ruta nueva, y menos atractivo si aún hay
            # muchos clientes con demanda alta por asignar.
            rem_pressure = 0.0
            rem_count = 0
            for c in remaining:
                rem_pressure += float(self.inst.demand[c]) / cap
                rem_count += 1
            rem_pressure = rem_pressure / max(rem_count, 1)

            return self.close_empty_penalty * unused + 0.25 * rem_pressure

        c = int(action[1])
        demand_c = float(self.inst.demand[c])
        radial_c = float(self.inst.dist(0, c))

        # Medida de "banda radial" de la ruta abierta: cuanto más homogénea sea la
        # distancia al depósito dentro de la ruta, más favorable.
        if open_route:
            rad_min = float(self.inst.dist(0, open_route[0]))
            rad_max = rad_min
            load = 0.0
            for x in open_route:
                dx = float(self.inst.dist(0, x))
                if dx < rad_min:
                    rad_min = dx
                if dx > rad_max:
                    rad_max = dx
                load += float(self.inst.demand[x])
            band = (rad_max - rad_min) / max(rad_max + rad_min, 1e-9)
            fill = load / cap

            last = open_route[-1]
            marginal = (
                float(self.inst.dist(last, c))
                + float(self.inst.dist(c, 0))
                - float(self.inst.dist(last, 0))
            )

            # Preferimos extender rutas con clientes de radio similar al tramo actual
            # y con demanda que deje la capacidad en una zona razonable.
            radial_band = abs(radial_c - 0.5 * (rad_min + rad_max)) / max(radial_c + rad_min + rad_max, 1e-9)
            projected_fill = min((load + demand_c) / cap, 2.0)
            balance_target = abs(projected_fill - 0.75)

            # Usamos también información del "frente" restante para sesgar a clientes
            # cuya inserción no empeore demasiado el conjunto pendiente.
            rem_avg_rad = 0.0
            rem_n = 0
            for r in remaining:
                rem_avg_rad += float(self.inst.dist(0, r))
                rem_n += 1
            rem_avg_rad = rem_avg_rad / max(rem_n, 1)
            future_bias = abs(radial_c - rem_avg_rad) / max(rem_avg_rad + radial_c, 1e-9)

            return (
                marginal
                + self.radial_weight * (radial_band + 0.5 * future_bias)
                + self.balance_weight * (balance_target + 0.25 * band)
                - 0.1 * fill
            )

        # Inicio de una nueva ruta: no solo importar cercanía al depósito, sino
        # también preferir clientes que actúan como "anclas" de demanda.
        rem_demand_avg = 0.0
        rem_rad_avg = 0.0
        rem_n = 0
        for r in remaining:
            rem_demand_avg += float(self.inst.demand[r])
            rem_rad_avg += float(self.inst.dist(0, r))
            rem_n += 1
        rem_demand_avg = rem_demand_avg / max(rem_n, 1)
        rem_rad_avg = rem_rad_avg / max(rem_n, 1)

        anchor = abs(demand_c - rem_demand_avg) / cap
        radial_gap = abs(radial_c - rem_rad_avg) / max(rem_rad_avg + radial_c, 1e-9)

        return self.radial_weight * radial_gap + self.balance_weight * anchor + 0.5 * radial_c / cap


def build_component(
    problem,
    radial_weight: float = 1.0,
    balance_weight: float = 1.0,
    close_empty_penalty: float = 3.0,
):
    return RadialDemandBalanceScore(
        problem,
        radial_weight=radial_weight,
        balance_weight=balance_weight,
        close_empty_penalty=close_empty_penalty,
    )


def score(self, partial, action) -> float:
    built, open_route, remaining = partial
    kind = action[0]

    cap = max(float(self.inst.capacity), 1e-9)

    if kind == "close":
        if not open_route:
            return inf
        load = 0.0
        for c in open_route:
            load += float(self.inst.demand[c])

        # Cerrar una ruta es mejor cuando la ruta ya está razonablemente cargada.
        fill = load / cap

        # Sesgo simple pero global: si aún quedan clientes con demanda alta,
        # penalizamos cerrar demasiado pronto para evitar fragmentar la solución.
        rem_avg_demand = 0.0
        rem_n = 0
        for r in remaining:
            rem_avg_demand += float(self.inst.demand[r])
            rem_n += 1
        rem_avg_demand = rem_avg_demand / max(rem_n, 1)

        return self.close_empty_penalty * (1.0 - min(fill, 1.0)) + 0.25 * (rem_avg_demand / cap)

    c = int(action[1])
    demand_c = float(self.inst.demand[c])
    radial_c = float(self.inst.dist(0, c))

    # Idea distinta: en vez de mirar la cercanía al último cliente, usamos una
    # puntuación "de partición" del gran tour. Queremos que los clientes elegidos
    # ayuden a formar bloques de demanda más homogéneos en el orden final del tour.
    rem_demand_avg = 0.0
    rem_rad_avg = 0.0
    rem_n = 0
    for r in remaining:
        rem_demand_avg += float(self.inst.demand[r])
        rem_rad_avg += float(self.inst.dist(0, r))
        rem_n += 1
    rem_demand_avg = rem_demand_avg / max(rem_n, 1)
    rem_rad_avg = rem_rad_avg / max(rem_n, 1)

    # "Ancla" de demanda: preferimos clientes cuya demanda se aleje del promedio
    # restante para que el split pueda formar segmentos más compactos.
    demand_anchor = abs(demand_c - rem_demand_avg) / cap

    # "Ancla" radial: preferimos extremos radiales (muy cerca o muy lejos del depot)
    # para que el gran tour no se parezca a una construcción por inserción local.
    radial_anchor = abs(radial_c - rem_rad_avg) / max(radial_c + rem_rad_avg, 1e-9)

    # Si la ruta abierta ya existe, premiamos que el cliente encaje en el perfil
    # agregado de la ruta (carga actual), no en su último arco.
    route_fill = 0.0
    route_rad_avg = 0.0
    route_n = 0
    for x in open_route:
        route_fill += float(self.inst.demand[x])
        route_rad_avg += float(self.inst.dist(0, x))
        route_n += 1

    if route_n > 0:
        route_fill = route_fill / cap
        route_rad_avg = route_rad_avg / route_n
        route_profile = abs(radial_c - route_rad_avg) / max(radial_c + route_rad_avg, 1e-9)
        balance_target = abs(min((route_fill + demand_c / cap), 1.5) - 0.70)
        return (
            self.radial_weight * radial_anchor
            + self.balance_weight * (demand_anchor + 0.5 * balance_target)
            + 0.25 * route_profile
        )

    # Inicio de una ruta: elegir clientes que actúan como separadores estructurales
    # del gran tour, no como simples vecinos del depósito.
    return self.radial_weight * radial_anchor + self.balance_weight * demand_anchor + 0.2 * (radial_c / cap)
