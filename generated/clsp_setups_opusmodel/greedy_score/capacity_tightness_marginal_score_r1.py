COMPONENT = {
    "name": "capacity_tightness_marginal_score",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "tight_weight": {"type": "float", "range": [0.0, 3.0]},
        "time_weight": {"type": "float", "range": [0.0, 2.0]},
    },
}


class CapacityTightnessMarginalScore:
    """Costo marginal ajustado por la carga de capacidad.
    'on' en (i,t): s[i] inflado por la utilización estimada de t (demanda del período más setups
    ya decididos más el propio). Se añade el tiempo de setup valorado al holding medio de la
    demanda de i en t.
    'off': inventario extra de traer d[i][t] desde el último setup L, inflado por la utilización
    de L, pues esa producción adelantada consume capacidad de L. Menor = mejor."""

    def __init__(self, problem, tight_weight: float = 1.0, time_weight: float = 0.5):
        inst = problem.inst
        self.inst = inst
        self.n = inst.n_items
        self.T = inst.n_periods
        self.tight_weight = float(tight_weight)
        self.time_weight = float(time_weight)
        self.dem_t = [sum(float(inst.demand[j][t]) for j in range(self.n)) for t in range(self.T)]

    def _util(self, partial, t, upto, extra):
        n = self.n
        inst = self.inst
        load = self.dem_t[t] + extra
        base = t * n
        for j in range(upto):
            idx = base + j
            if idx < len(partial) and partial[idx]:
                load += float(inst.setup_time[j])
        cap = max(float(inst.capacity[t]), 1e-9)
        return min(load / cap, 10.0)

    def score(self, partial, action):
        kind, i, t = action[0], int(action[1]), int(action[2])
        inst = self.inst
        n = self.n
        if kind == "on":
            st = float(inst.setup_time[i])
            u = self._util(partial, t, i, st)
            h = float(inst.holding_cost[i])
            time_pen = self.time_weight * st * h
            return float(inst.setup_cost[i]) * (1.0 + self.tight_weight * u) + time_pen
        extra_hold = float(action[6]) if len(action) > 6 else 0.0
        L = -1
        for tt in range(t - 1, -1, -1):
            idx = tt * n + i
            if idx < len(partial) and partial[idx]:
                L = tt
                break
        if L < 0:
            return extra_hold
        uL = self._util(partial, L, n, 0.0)
        return extra_hold * (1.0 + self.tight_weight * uL)


def build_component(problem, tight_weight: float = 1.0, time_weight: float = 0.5):
    return CapacityTightnessMarginalScore(problem, tight_weight, time_weight)
