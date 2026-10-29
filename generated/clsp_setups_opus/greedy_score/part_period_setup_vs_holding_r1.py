COMPONENT = {
    "name": "part_period_setup_vs_holding",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "holding_weight": {"type": "float", "range": [0.5, 2.0]},
        "lookahead": {"type": "int", "range": [0, 3]},
    },
}


class PartPeriodSetupVsHolding:
    """Acción (i, t, val): val=True abre setup del ítem i en t. Puntaje True = s[i];
    puntaje False = costo de inventario de cubrir d[i][t] (y opcionalmente unos períodos
    siguientes que heredarían el lote) desde el último setup del ítem. Menor = mejor."""

    def __init__(self, problem, holding_weight=1.0, lookahead=1):
        inst = problem.inst
        self.n_periods = inst.n_periods
        self.demand = [[float(d) for d in row] for row in inst.demand]
        self.s = [float(x) for x in inst.setup_cost]
        self.h = [float(x) for x in inst.holding_cost]
        self.w = float(holding_weight)
        self.look = int(lookahead)

    def _last_setup(self, partial, i, t):
        row = partial[i]
        for k in range(t - 1, -1, -1):
            v = row[k]
            if v is None or v:
                return k
        return None

    def score(self, partial, action):
        i, t, val = action[0], action[1], bool(action[2])
        d = self.demand[i]
        last = self._last_setup(partial, i, t)
        if last is None:
            # sin setup previo: solo conviene no abrir si no hay demanda
            hold = 0.0 if d[t] <= 1e-9 else 1e12
        else:
            hold = self.h[i] * d[t] * (t - last)
            # mirada adelante: el lote previo también tendría que cubrir períodos siguientes
            disc = 0.5
            for k in range(1, self.look + 1):
                tt = t + k
                if tt >= self.n_periods:
                    break
                hold += disc * self.h[i] * d[tt] * (tt - last)
                disc *= 0.5
        if val:
            return float(self.s[i])
        return float(min(self.w * hold, 1e12))


def build_component(problem, holding_weight: float = 1.0, lookahead: int = 1):
    return PartPeriodSetupVsHolding(problem, holding_weight, lookahead)
