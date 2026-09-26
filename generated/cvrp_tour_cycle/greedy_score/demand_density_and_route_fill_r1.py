COMPONENT = {
    "name": "demand_density_and_route_fill",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "capacity_weight": {"type": "float", "range": [0.0, 10.0]},
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "fill_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class DemandDensityAndRouteFill:
    """CVRP tour: favorece clientes "densos" por demanda (mucha demanda por poca distancia)
    y, además, tender a completar la capacidad de la ruta abierta antes de cerrarla.
    Menor puntaje = mejor."""

    def __init__(self, problem, capacity_weight: float = 1.0, distance_weight: float = 1.0, fill_weight: float = 1.0):
        self.inst = problem.inst
        self.capacity_weight = float(capacity_weight)
        self.distance_weight = float(distance_weight)
        self.fill_weight = float(fill_weight)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]
        cap = float(self.inst.capacity)

        if kind == "close":
            if not open_route:
                return 0.0
            load = sum(self.inst.demand[c] for c in open_route)
            fill_ratio = load / cap if cap > 0 else 0.0
            # Closing is better when the route is already well filled.
            return self.fill_weight * (1.0 - fill_ratio)

        c = int(action[1])
        demand = float(self.inst.demand[c])

        if not open_route:
            # Starting a route: prefer high-demand customers close to the depot.
            base = self.inst.dist(0, c)
            density = demand / max(base, 1e-9)
            return self.distance_weight * base - self.capacity_weight * density

        last = open_route[-1]
        added = self.inst.dist(last, c) + self.inst.dist(c, 0) - self.inst.dist(last, 0)

        current_load = sum(self.inst.demand[x] for x in open_route)
        new_load = current_load + demand
        fill_ratio = new_load / cap if cap > 0 else 0.0
        slack_after = max(0.0, cap - new_load)

        density = demand / max(added, 1e-9)
        return self.distance_weight * added - self.capacity_weight * density + self.fill_weight * (slack_after / max(cap, 1e-9) + (1.0 - min(fill_ratio, 1.0)))


def build_component(problem, capacity_weight: float = 1.0, distance_weight: float = 1.0, fill_weight: float = 1.0):
    return DemandDensityAndRouteFill(problem, capacity_weight=capacity_weight, distance_weight=distance_weight, fill_weight=fill_weight)
