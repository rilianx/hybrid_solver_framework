import math

COMPONENT = {
    "name": "far_seed_best_fit_fill",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "fill_weight": {"type": "float", "range": [0.0, 3.0]},
        "seed_rule": {"type": "cat", "values": ["farthest", "largest_demand"]},
    },
}

_CLOSE_SCORE = 1e12


class FarSeedBestFitFill:
    """Al abrir una ruta, la semilla es el cliente más lejano al depósito (o el de mayor
    demanda): los clientes difíciles se atienden primero, cuando hay más libertad. Con la
    ruta abierta, puntaje = costo marginal normalizado + fill_weight * (capacidad libre
    que quedaría / capacidad): prefiere completar el vehículo de forma ajustada (best-fit),
    lo que reduce la cantidad de rutas y los tramos al depósito."""

    def __init__(self, problem, fill_weight: float = 0.5, seed_rule: str = "farthest"):
        self.inst = problem.inst
        self.fill_weight = float(fill_weight)
        self.seed_rule = seed_rule if seed_rule in ("farthest", "largest_demand") else "farthest"
        custs = list(self.inst.customers)
        self.d0 = {int(c): float(self.inst.dist(0, c)) for c in custs}
        tot = sum(self.d0.values())
        self.scale = tot / len(custs) if custs and tot > 0 else 1.0
        cap = float(self.inst.capacity)
        self.cap = cap if cap > 0 else 1.0

    def score(self, partial, action):
        if action[0] != "add":
            return _CLOSE_SCORE
        c = int(action[1])
        inst = self.inst
        open_route = partial[1]
        dc = float(inst.demand[c])
        if not open_route:
            if self.seed_rule == "farthest":
                val = -self.d0.get(c, 0.0) / self.scale - 1e-3 * dc / self.cap
            else:
                val = -dc / self.cap - 1e-3 * self.d0.get(c, 0.0) / self.scale
        else:
            last = open_route[-1]
            dist = inst.dist
            delta = dist(last, c) + dist(c, 0) - dist(last, 0)
            load = 0.0
            for x in open_route:
                load += inst.demand[x]
            residual = max(0.0, self.cap - load - dc) / self.cap
            val = delta / self.scale + self.fill_weight * residual
        if not math.isfinite(val):
            return _CLOSE_SCORE / 2.0
        return float(val)


def build_component(problem, fill_weight: float = 0.5, seed_rule: str = "farthest"):
    return FarSeedBestFitFill(problem, fill_weight, seed_rule)
