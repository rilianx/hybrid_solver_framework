COMPONENT = {
    "name": "density_and_capacity_pressure",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "distance_weight": {"type": "float", "range": [0.0, 5.0]},
        "pressure_weight": {"type": "float", "range": [0.0, 5.0]},
        "slack_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class DensityAndCapacityPressure:
    """CVRP: combina distancia, presión de capacidad y densidad de carga.
    Favorece clientes cercanos, grandes demandas y elecciones que dejan poca holgura.
    Menor puntaje = mejor."""

    def __init__(self, problem, distance_weight: float = 1.0, pressure_weight: float = 1.0, slack_weight: float = 0.5):
        self.inst = problem.inst
        self.distance_weight = float(distance_weight)
        self.pressure_weight = float(pressure_weight)
        self.slack_weight = float(slack_weight)

    def score(self, partial, action) -> float:
        inst = self.inst
        c = int(action)
        current = getattr(partial, "current", ())
        prev = int(current[-1]) if current else 0

        demand = float(inst.demand[c])
        capacity = max(float(inst.capacity), 1e-9)
        dist_prev = float(inst.dist(prev, c))

        current_load = 0.0
        for node in current:
            current_load += float(inst.demand[int(node)])
        remaining_cap = max(capacity - current_load, 1e-9)

        density = demand / max(dist_prev, 1e-9)
        pressure = demand / remaining_cap
        slack_term = remaining_cap / capacity

        return (
            self.distance_weight * dist_prev
            - self.pressure_weight * pressure
            - self.slack_weight * density
            + 0.1 * slack_term
        )


def build_component(problem, distance_weight: float = 1.0, pressure_weight: float = 1.0, slack_weight: float = 0.5):
    return DensityAndCapacityPressure(
        problem,
        distance_weight=distance_weight,
        pressure_weight=pressure_weight,
        slack_weight=slack_weight,
    )
