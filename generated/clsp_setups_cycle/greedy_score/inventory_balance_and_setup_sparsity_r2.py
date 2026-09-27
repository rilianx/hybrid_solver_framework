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
        self._future_demand = self._compute_future_demand()
        self._total_demand = self._compute_total_demand()

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
        inst = self.inst
        n_items = max(inst.n_items, 1)
        n_periods = max(inst.n_periods, 1)

        setup_cost = float(inst.setup_cost[i])
        hold_cost = float(inst.holding_cost[i])

        # Urgencia de cobertura: demanda futura aún pendiente desde t.
        future_mass = float(self._future_demand[i][t])
        remaining_horizon = max(n_periods - t, 1)
        demand_density = future_mass / remaining_horizon

        # Ítems caros de mantener: más urgente abrirlos antes si tienen demanda futura.
        inventory_pressure = hold_cost * demand_density

        # Penaliza concentrar demasiados setups en el mismo período.
        period_load = self._count_setups_in_period(partial, t)
        balanced_setup = period_load / n_items

        # Favorece setups en periodos tempranos solo cuando hay carga futura real.
        early_bias = (n_periods - 1 - t) / max(n_periods - 1, 1)

        if val:
            score = self.inventory_weight * inventory_pressure
            score += self.sparsity_weight * setup_cost * balanced_setup
            score += self.early_setup_weight * setup_cost * early_bias
            # Si la demanda futura del ítem es pequeña, abrir setup es menos atractivo.
            score += 0.01 * setup_cost / max(self._total_demand, 1.0)
        else:
            # Cerrar/no activar es mejor cuando el ítem tiene poca presión de inventario
            # y el período ya está cargado.
            score = self.inventory_weight * 0.5 * inventory_pressure
            score += self.sparsity_weight * setup_cost * (1.0 - balanced_setup)
            score -= self.early_setup_weight * 0.05 * setup_cost * early_bias
        return score

    def _compute_total_demand(self):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        total = 0.0
        for i in range(n_items):
            for t in range(n_periods):
                total += float(inst.demand[i][t])
        return total

    def _compute_future_demand(self):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        future = [[0.0] * n_periods for _ in range(n_items)]
        for i in range(n_items):
            acc = 0.0
            for t in range(n_periods - 1, -1, -1):
                acc += float(inst.demand[i][t])
                future[i][t] = acc
        return future

    def _count_setups_in_period(self, partial, t):
        if partial is None:
            return 0
        count = 0
        try:
            for item_plan in partial:
                if t < len(item_plan) and bool(item_plan[t]):
                    count += 1
        except Exception:
            return 0
        return count


def build_component(problem, inventory_weight: float = 1.0, sparsity_weight: float = 1.0, early_setup_weight: float = 0.5):
    return InventoryBalanceAndSetupSparsity(
        problem,
        inventory_weight=inventory_weight,
        sparsity_weight=sparsity_weight,
        early_setup_weight=early_setup_weight,
    )
