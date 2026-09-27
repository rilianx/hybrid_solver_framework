COMPONENT = {
    "name": "capacity_pressure_with_demand_horizon",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "capacity_weight": {"type": "float", "range": [0.0, 10.0]},
        "demand_weight": {"type": "float", "range": [0.0, 10.0]},
        "setup_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class CapacityPressureWithDemandHorizon:
    """Greedy constructivo para CLSP.
    Idea: favorece abrir setups en períodos con mayor presión de capacidad
    (poca capacidad y setups caros en tiempo) y mayor demanda futura acumulada.
    Menor score = mejor."""

    __slots__ = (
        "inst",
        "capacity_weight",
        "demand_weight",
        "setup_weight",
        "_future_demand",
        "_capacity",
        "_setup_time",
        "_setup_cost",
    )

    def __init__(self, problem, capacity_weight: float = 1.0, demand_weight: float = 1.0, setup_weight: float = 0.5):
        inst = problem.inst
        self.inst = inst
        self.capacity_weight = capacity_weight
        self.demand_weight = demand_weight
        self.setup_weight = setup_weight

        # Cache de accesos frecuentes para reducir coste por llamada a score().
        self._capacity = tuple(float(x) for x in inst.capacity)
        self._setup_time = tuple(float(x) for x in inst.setup_time)
        self._setup_cost = tuple(float(x) for x in inst.setup_cost)

        # Precomputo de demanda futura acumulada, almacenado como tuplas inmutables.
        demand = inst.demand
        n_items = inst.n_items
        n_periods = inst.n_periods
        future = []
        for i in range(n_items):
            row = [0.0] * n_periods
            running = 0.0
            demand_i = demand[i]
            for t in range(n_periods - 1, -1, -1):
                running += float(demand_i[t])
                row[t] = running
            future.append(tuple(row))
        self._future_demand = tuple(future)

    def score(self, partial, action) -> float:
        i, t, val = action

        # Accesos locales para minimizar overhead en una función hot-path.
        cap = self._capacity[t]
        setup_time = self._setup_time[i]
        demand_future = self._future_demand[i][t]
        setup_cost = self._setup_cost[i]

        cap_pressure = setup_time / max(cap, 1e-9)

        score = self.capacity_weight * cap_pressure + self.demand_weight * demand_future
        score += self.setup_weight * setup_cost
        if not val:
            score += 0.25 * (self.capacity_weight * cap_pressure)
        return score


def build_component(problem, capacity_weight: float = 1.0, demand_weight: float = 1.0, setup_weight: float = 0.5):
    return CapacityPressureWithDemandHorizon(
        problem,
        capacity_weight=capacity_weight,
        demand_weight=demand_weight,
        setup_weight=setup_weight,
    )
