import math

COMPONENT = {
    "name": "savings_isolation_seed_far",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "isolation_weight": {"type": "float", "range": [0.0, 1.0]},
        "fill_weight": {"type": "float", "range": [0.0, 1.0]},
        "close_margin": {"type": "float", "range": [0.01, 1.0]},
    },
}


class SavingsIsolationSeedFar:
    """add con ruta abierta: -(d(last,0)+d(0,c)-d(last,c)) (ahorro CW, negado).
    add con ruta vacía: -d(0,c) (siembra con el más lejano). En ambos casos se resta
    isolation_weight·(distancia al vecino más cercano de c), para atender pronto a los aislados,
    y se suma fill_weight·escala·(capacidad libre tras c)/Q.
    close: mejor 'add' factible + margen."""

    def __init__(self, problem, isolation_weight=0.3, fill_weight=0.2, close_margin=0.1):
        inst = problem.inst
        self.inst = inst
        self.iw = float(isolation_weight)
        self.fw = float(fill_weight)
        self.margin = float(close_margin)
        self.Q = max(float(inst.capacity), 1e-9)
        self.cap = float(inst.capacity) + 1e-9
        custs = list(inst.customers)
        self.iso = {}
        for c in custs:
            best = None
            for o in custs:
                if o != c:
                    dd = inst.dist(c, o)
                    if best is None or dd < best:
                        best = dd
            self.iso[c] = best if best is not None else 0.0
        self.scale = (sum(inst.dist(0, c) for c in custs) / len(custs)) if custs else 1.0
        if not (self.scale > 0) or not math.isfinite(self.scale):
            self.scale = 1.0

    def _add_score(self, last, load, c):
        inst = self.inst
        if last == 0:
            base = -inst.dist(0, c)
        else:
            base = -(inst.dist(last, 0) + inst.dist(0, c) - inst.dist(last, c))
        free = max(self.Q - (load + inst.demand[c]), 0.0) / self.Q
        return base - self.iw * self.iso[c] + self.fw * self.scale * free

    def score(self, partial, action):
        closed, cur, load, remaining = partial
        last = cur[-1] if cur else 0
        if action[0] == "close":
            best = None
            for c in remaining:
                if load + self.inst.demand[c] <= self.cap:
                    s = self._add_score(last, load, c)
                    if best is None or s < best:
                        best = s
            if best is None:
                return 0.0
            return float(best + self.margin * (abs(best) + self.scale))
        return float(self._add_score(last, load, int(action[1])))


def build_component(problem, isolation_weight=0.3, fill_weight=0.2, close_margin=0.1):
    return SavingsIsolationSeedFar(problem, isolation_weight, fill_weight, close_margin)
