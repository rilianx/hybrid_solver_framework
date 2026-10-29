COMPONENT = {
    "name": "part_period_balancing_score",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {"setup_weight": {"type": "float", "range": [0.3, 3.0]}},
}


class PartPeriodBalancingScore:
    """Acción = (tipo, i, t, s, st, dem, extra_hold); parcial = tupla de bool ordenada por (t, i).
    'off' cuesta el inventario ACUMULADO del lote abierto (desde el último setup hasta t inclusive);
    'on' cuesta setup_weight * s[i]. Extiende el lote mientras el inventario acumulado no supere
    el setup (regla de balanceo parte-período). Menor = mejor."""

    def __init__(self, problem, setup_weight: float = 1.0):
        self.inst = problem.inst
        self.n = problem.inst.n_items
        self.setup_weight = float(setup_weight)

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
        if kind == "on":
            return self.setup_weight * s
        L = self._last_on(partial, i, t)
        if L < 0:
            return float(action[6]) if len(action) > 6 else 0.0
        h = float(inst.holding_cost[i])
        cum = 0.0
        row = inst.demand[i]
        for k in range(L + 1, t + 1):
            cum += h * float(row[k]) * (k - L)
        return cum


def build_component(problem, setup_weight: float = 1.0):
    return PartPeriodBalancingScore(problem, setup_weight)
