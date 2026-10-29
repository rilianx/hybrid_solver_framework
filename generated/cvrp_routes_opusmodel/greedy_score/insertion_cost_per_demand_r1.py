import math

COMPONENT = {
    "name": "insertion_cost_per_demand",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "demand_power": {"type": "float", "range": [0.0, 1.0]},
        "close_margin": {"type": "float", "range": [0.01, 1.0]},
    },
}


class InsertionCostPerDemand:
    """Acción ("add", c, delta, newload) | ("close", None, 0, 0). Parcial = (closed, cur, load, remaining).
    add: desvío de insertar c antes del regreso al depósito, dividido por d[c]^p (costo por unidad servida).
    close: mejor puntaje 'add' factible más un margen, para cerrar solo cuando ya no cabe nada."""

    def __init__(self, problem, demand_power=0.3, close_margin=0.1):
        inst = problem.inst
        self.inst = inst
        self.p = float(demand_power)
        self.margin = float(close_margin)
        self.cap = float(inst.capacity) + 1e-9
        custs = list(inst.customers)
        self.scale = (sum(inst.dist(0, c) for c in custs) / len(custs)) if custs else 1.0
        if not (self.scale > 0) or not math.isfinite(self.scale):
            self.scale = 1.0

    def _add_score(self, last, c):
        inst = self.inst
        delta = inst.dist(last, c) + inst.dist(c, 0) - inst.dist(last, 0)
        d = max(float(inst.demand[c]), 1e-9)
        return max(delta, 0.0) / (d ** self.p)

    def score(self, partial, action):
        closed, cur, load, remaining = partial
        last = cur[-1] if cur else 0
        if action[0] == "close":
            best = None
            for c in remaining:
                if load + self.inst.demand[c] <= self.cap:
                    s = self._add_score(last, c)
                    if best is None or s < best:
                        best = s
            if best is None:
                return 0.0
            return float(best + self.margin * (abs(best) + self.scale))
        return float(self._add_score(last, int(action[1])))


def build_component(problem, demand_power=0.3, close_margin=0.1):
    return InsertionCostPerDemand(problem, demand_power, close_margin)
