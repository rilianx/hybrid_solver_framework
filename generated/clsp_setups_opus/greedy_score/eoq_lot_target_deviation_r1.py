import math

COMPONENT = {
    "name": "eoq_lot_target_deviation",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "eoq_scale": {"type": "float", "range": [0.5, 2.0]},
        "asym": {"type": "float", "range": [0.5, 2.0]},
    },
}


class EoqLotTargetDeviation:
    """Acción (i, t, val). Para cada ítem calcula el lote económico Q* = sqrt(2 s D / h)
    con D la demanda media. Lote previo = demanda acumulada desde el último setup.
    True cierra el lote con la demanda hasta t-1; False lo extiende con d[i][t].
    Puntaje = desvío relativo del lote resultante respecto a Q* (los excesos se
    ponderan con `asym`). Menor = mejor."""

    def __init__(self, problem, eoq_scale=1.0, asym=1.0):
        inst = problem.inst
        self.n_periods = inst.n_periods
        self.demand = [[float(d) for d in row] for row in inst.demand]
        self.asym = float(asym)
        self.q = []
        for i in range(inst.n_items):
            s = float(inst.setup_cost[i])
            h = float(inst.holding_cost[i])
            dm = sum(self.demand[i]) / max(1, self.n_periods)
            if h <= 1e-12 or dm <= 1e-12:
                q = max(sum(self.demand[i]), 1.0) * 10.0
            else:
                q = math.sqrt(2.0 * s * dm / h)
            self.q.append(max(float(eoq_scale) * q, 1e-6))

    def _dev(self, lot, q):
        r = (lot - q) / q
        return self.asym * r if r > 0 else -r

    def score(self, partial, action):
        i, t, val = action[0], action[1], bool(action[2])
        d = self.demand[i]
        row = partial[i]
        last = None
        for k in range(t - 1, -1, -1):
            v = row[k]
            if v is None or v:
                last = k
                break
        if last is None:
            if d[t] <= 1e-9:
                return 1.0 if val else 0.0
            return 0.0 if val else 1e6
        cum_prev = 0.0
        for k in range(last, t):
            cum_prev += d[k]
        q = self.q[i]
        if val:
            # cierra el lote previo y abre uno nuevo; ligero sesgo si t no tiene demanda
            base = self._dev(cum_prev, q)
            return float(min(base + (0.5 if d[t] <= 1e-9 else 0.0), 1e6))
        return float(min(self._dev(cum_prev + d[t], q), 1e6))


def build_component(problem, eoq_scale: float = 1.0, asym: float = 1.0):
    return EoqLotTargetDeviation(problem, eoq_scale, asym)
