COMPONENT = {
    "name": "high_demand_urgent_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "demand_weight": {"type": "float", "range": [0.0, 10.0]},
        "balance_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class HighDemandUrgentScore:
    """CVRP greedy score: prioriza clientes de alta demanda cuando la ruta aún tiene
    capacidad suficiente, y penaliza elegir clientes que desequilibran mucho la carga
    actual respecto a la capacidad del vehículo. Menor puntaje = mejor."""

    def __init__(self, problem, demand_weight: float = 1.0, balance_weight: float = 0.5):
        self.inst = problem.inst
        self.demand_weight = float(demand_weight)
        self.balance_weight = float(balance_weight)

    def score(self, partial, action):
        inst = self.inst
        c = int(action)
        d = float(inst.demand[c])

        current_load = 0.0
        if getattr(partial, "current", ()):
            for x in partial.current:
                current_load += float(inst.demand[int(x)])

        remaining_after = max(float(inst.capacity) - current_load - d, 0.0)
        fill_ratio = (current_load + d) / max(float(inst.capacity), 1e-9)

        # Larger demand => smaller score; more leftover slack => slightly better.
        demand_term = -self.demand_weight * d
        balance_term = self.balance_weight * abs(0.5 - fill_ratio)
        slack_term = 0.1 * remaining_after / max(float(inst.capacity), 1e-9)
        return demand_term + balance_term + slack_term


def build_component(problem, demand_weight: float = 1.0, balance_weight: float = 0.5):
    return HighDemandUrgentScore(problem, demand_weight=demand_weight, balance_weight=balance_weight)
