COMPONENT = {
    "name": "inventory_balance_and_setup_sparsity",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "inventory_weight": {"type": "float", "range": [0.0, 10.0]},
        "sparsity_weight": {"type": "float", "range": [0.0, 10.0]},
        "early_setup_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class InventoryBalanceAndSetupSparsity:
    """Greedy constructivo para CLSP.
    Idea: prefiere decisiones que mantengan un plan de setups equilibrado a lo largo
    del tiempo, evitando concentrar demasiados True en períodos tempranos y dando
    prioridad a ítems con inventario potencial alto.
    Menor score = mejor."""

    def __init__(self, problem, inventory_weight: float = 1.0, sparsity_weight: float = 1.0, early_setup_weight: float = 0.5):
        self.inst = problem.inst
        self.inventory_weight = inventory_weight
        self.sparsity_weight = sparsity_weight
        self.early_setup_weight = early_setup_weight
        self._avg_demand = self._compute_avg_demand()

    def _compute_avg_demand(self):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        avg = [0.0] * n_items
        for i in range(n_items):
            total = 0.0
            for t in range(n_periods):
                total += float(inst.demand[i][t])
            avg[i] = total / max(n_periods, 1)
        return avg

    def score(self, partial, action) -> float:
        i, t, val = action
        setup_cost = float(self.inst.setup_cost[i])
        hold_cost = float(self.inst.holding_cost[i])
        avg_dem = float(self._avg_demand[i])

        # Ítems caros de mantener: tender a decidirlos antes si son relevantes.
        inventory_pressure = hold_cost * avg_dem
        # Penaliza poner demasiados setups temprano.
        early_penalty = (self.inst.n_periods - t) / max(self.inst.n_periods, 1)
        # Pequeña preferencia por no abrir setup si no aporta estructura.
        sparsity = 1.0 if val else 0.0

        score = self.inventory_weight * inventory_pressure
        score += self.sparsity_weight * setup_cost * sparsity
        score += self.early_setup_weight * setup_cost * early_penalty * sparsity
        if not val:
            score -= 0.1 * self.sparsity_weight * setup_cost
        return score


def build_component(problem, inventory_weight: float = 1.0, sparsity_weight: float = 1.0, early_setup_weight: float = 0.5):
    return InventoryBalanceAndSetupSparsity(
        problem,
        inventory_weight=inventory_weight,
        sparsity_weight=sparsity_weight,
        early_setup_weight=early_setup_weight,
    )
