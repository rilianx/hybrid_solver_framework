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

    def __init__(self, problem, capacity_weight: float = 1.0, demand_weight: float = 1.0, setup_weight: float = 0.5):
        self.inst = problem.inst
        self.capacity_weight = capacity_weight
        self.demand_weight = demand_weight
        self.setup_weight = setup_weight
        self._future_demand = self._compute_future_demand()

    def _compute_future_demand(self):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        fut = [[0.0] * n_periods for _ in range(n_items)]
        for i in range(n_items):
            running = 0.0
            for t in range(n_periods - 1, -1, -1):
                running += float(inst.demand[i][t])
                fut[i][t] = running
        return fut

    def score(self, partial, action) -> float:
        i, t, val = action
        cap = float(self.inst.capacity[t])
        setup_time = float(self.inst.setup_time[i])
        demand_future = float(self._future_demand[i][t])

        cap_pressure = setup_time / max(cap, 1e-9)
        demand_pressure = demand_future
        setup_cost = float(self.inst.setup_cost[i])

        score = self.capacity_weight * cap_pressure + self.demand_weight * demand_pressure
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
