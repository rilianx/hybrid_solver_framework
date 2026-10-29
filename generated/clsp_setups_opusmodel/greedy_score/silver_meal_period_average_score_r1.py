COMPONENT = {
    "name": "silver_meal_period_average_score",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {"close_bias": {"type": "float", "range": [0.5, 2.0]}},
}


class SilverMealPeriodAverageScore:
    """Heurística Silver-Meal sobre el lote abierto del ítem i (desde su último setup L < t):
    'off' = costo medio por período si el lote se extiende para cubrir t;
    'on'  = close_bias * costo medio por período del lote actual (cerrarlo y abrir otro en t).
    Sin setup previo, 'on' vale s[i] y 'off' su sobrecosto (solo factible con demanda nula).
    Menor = mejor."""

    def __init__(self, problem, close_bias: float = 1.0):
        self.inst = problem.inst
        self.n = problem.inst.n_items
        self.close_bias = float(close_bias)

    def _last_on(self, partial, i, t):
        n = self.n
        for tt in range(t - 1, -1, -1):
            idx = tt * n + i
            if idx < len(partial) and partial[idx]:
                return tt
        return -1

    def score(self, partial, action):
        kind, i, t = action[0], int(action[1]), int(action[2])
        inst = self.inst
        s = float(inst.setup_cost[i])
        L = self._last_on(partial, i, t)
        if L < 0:
            if kind == "on":
                return s
            return float(action[6]) if len(action) > 6 else 0.0
        h = float(inst.holding_cost[i])
        row = inst.demand[i]
        hprev = 0.0
        for k in range(L + 1, t):
            hprev += h * float(row[k]) * (k - L)
        span = t - L
        avg_cur = (s + hprev) / span
        if kind == "on":
            return self.close_bias * avg_cur
        avg_ext = (s + hprev + h * float(row[t]) * (t - L)) / (span + 1)
        return avg_ext


def build_component(problem, close_bias: float = 1.0):
    return SilverMealPeriodAverageScore(problem, close_bias)
