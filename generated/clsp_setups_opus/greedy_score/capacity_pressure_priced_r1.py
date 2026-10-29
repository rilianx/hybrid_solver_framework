COMPONENT = {
    "name": "capacity_pressure_priced",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "pressure_weight": {"type": "float", "range": [0.0, 3.0]},
        "pressure_exp": {"type": "float", "range": [1.0, 3.0]},
    },
}


class CapacityPressurePriced:
    """Acción (i, t, val). Estima la utilización de cada período (demanda total +
    tiempos de setup aún abiertos en el parcial) y la convierte en costo con un precio
    por unidad de capacidad (~costo medio de inventario). True paga s[i] + tiempo de
    setup a precio de t; False paga inventario de llevar d[i][t] desde el último setup
    más la capacidad que consume en ese período. Menor = mejor."""

    def __init__(self, problem, pressure_weight=1.0, pressure_exp=2.0):
        inst = problem.inst
        self.n_items = inst.n_items
        self.n_periods = inst.n_periods
        self.demand = [[float(d) for d in row] for row in inst.demand]
        self.cap = [max(float(c), 1e-9) for c in inst.capacity]
        self.st = [float(x) for x in inst.setup_time]
        self.s = [float(x) for x in inst.setup_cost]
        self.h = [float(x) for x in inst.holding_cost]
        self.beta = float(pressure_weight)
        self.exp = float(pressure_exp)
        self.price = sum(self.h) / max(1, len(self.h))
        self.dem_load = [sum(self.demand[i][t] for i in range(self.n_items)) for t in range(self.n_periods)]

    def _rho(self, partial, t):
        load = self.dem_load[t]
        for i in range(self.n_items):
            v = partial[i][t]
            if v is None or v:
                load += self.st[i]
        r = load / self.cap[t]
        return min(max(r, 0.0), 10.0) ** self.exp

    def _last_setup(self, partial, i, t):
        row = partial[i]
        for k in range(t - 1, -1, -1):
            v = row[k]
            if v is None or v:
                return k
        return None

    def score(self, partial, action):
        i, t, val = action[0], action[1], bool(action[2])
        if val:
            return float(self.s[i] + self.beta * self._rho(partial, t) * self.st[i] * self.price)
        d = self.demand[i][t]
        if d <= 1e-9:
            return 0.0
        last = self._last_setup(partial, i, t)
        if last is None:
            return 1e12
        hold = self.h[i] * d * (t - last)
        cap_cost = self.beta * self._rho(partial, last) * d * self.price
        return float(min(hold + cap_cost, 1e12))


def build_component(problem, pressure_weight: float = 1.0, pressure_exp: float = 2.0):
    return CapacityPressurePriced(problem, pressure_weight, pressure_exp)
