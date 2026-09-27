from functools import lru_cache


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

        inst = self.inst
        self._n_items = inst.n_items
        self._n_periods = inst.n_periods
        self._n_items_safe = max(self._n_items, 1)
        self._n_periods_safe = max(self._n_periods, 1)
        self._n_periods_minus_1_safe = max(self._n_periods - 1, 1)
        self._total_demand = self._compute_total_demand()
        self._avg_demand = self._compute_avg_demand()
        self._future_demand = self._compute_future_demand()

        # Precalcula costos y factores por ítem/período para evitar trabajo repetido.
        self._setup_cost = [float(c) for c in inst.setup_cost]
        self._hold_cost = [float(c) for c in inst.holding_cost]
        self._early_bias = [(self._n_periods - 1 - t) / self._n_periods_minus_1_safe for t in range(self._n_periods)]

    def _compute_avg_demand(self):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        avg = [0.0] * n_items
        denom = max(n_periods, 1)
        for i in range(n_items):
            total = 0.0
            row = inst.demand[i]
            for t in range(n_periods):
                total += float(row[t])
            avg[i] = total / denom
        return avg

    def score(self, partial, action) -> float:
        i, t, val = action
        n_items_safe = self._n_items_safe
        n_periods_safe = self._n_periods_safe

        setup_cost = self._setup_cost[i]
        hold_cost = self._hold_cost[i]

        future_mass = self._future_demand[i][t]
        remaining_horizon = max(self._n_periods - t, 1)
        demand_density = future_mass / remaining_horizon

        inventory_pressure = hold_cost * demand_density

        period_load = self._count_setups_in_period(partial, t)
        balanced_setup = period_load / n_items_safe

        early_bias = self._early_bias[t]

        if val:
            score = self.inventory_weight * inventory_pressure
            score += self.sparsity_weight * setup_cost * balanced_setup
            score += self.early_setup_weight * setup_cost * early_bias
            score += 0.01 * setup_cost / max(self._total_demand, 1.0)
        else:
            score = self.inventory_weight * 0.5 * inventory_pressure
            score += self.sparsity_weight * setup_cost * (1.0 - balanced_setup)
            score -= self.early_setup_weight * 0.05 * setup_cost * early_bias
        return score

    def _compute_total_demand(self):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        total = 0.0
        for i in range(n_items):
            row = inst.demand[i]
            for t in range(n_periods):
                total += float(row[t])
        return total

    def _compute_future_demand(self):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        future = [[0.0] * n_periods for _ in range(n_items)]
        for i in range(n_items):
            acc = 0.0
            row = inst.demand[i]
            out = future[i]
            for t in range(n_periods - 1, -1, -1):
                acc += float(row[t])
                out[t] = acc
        return future

    @staticmethod
    def _as_tuple_partial(partial):
        if partial is None:
            return None
        if isinstance(partial, tuple):
            return partial
        return tuple(tuple(row) for row in partial)

    @lru_cache(maxsize=8192)
    def _count_setups_in_period_cached(self, partial_tuple, t):
        if partial_tuple is None:
            return 0
        count = 0
        try:
            for item_plan in partial_tuple:
                if t < len(item_plan) and bool(item_plan[t]):
                    count += 1
        except Exception:
            return 0
        return count

    def _count_setups_in_period(self, partial, t):
        return self._count_setups_in_period_cached(self._as_tuple_partial(partial), t)


def build_component(problem, inventory_weight: float = 1.0, sparsity_weight: float = 1.0, early_setup_weight: float = 0.5):
    return InventoryBalanceAndSetupSparsity(
        problem,
        inventory_weight=inventory_weight,
        sparsity_weight=sparsity_weight,
        early_setup_weight=early_setup_weight,
    )
