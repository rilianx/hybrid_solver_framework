COMPONENT = {
    "name": "farthest_seed_nearest_extend",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "fill_weight": {"type": "float", "range": [0.0, 1.0]},
    },
}


class FarthestSeedNearestExtend:
    """Estrategia de dos niveles. Toda continuación de la ruta abierta puntúa
    por debajo de cualquier apertura, gracias a un desplazamiento grande.
    Entre continuaciones gana el vecino más cercano al último nodo, con un leve
    premio por demanda. Entre aperturas gana el cliente más lejano al depósito,
    porque conviene atender primero a los difíciles."""

    def __init__(self, problem, fill_weight=0.2):
        inst = problem.inst
        self.inst = inst
        n = inst.n_customers
        self.dem = list(inst.demand)
        self.cap = float(inst.capacity) if inst.capacity > 0 else 1.0
        self.d0 = [0.0] + [float(inst.dist(0, c)) for c in range(1, n + 1)]
        maxd = 0.0
        coords = inst.coords
        if len(coords) > 1:
            xs = [p[0] for p in coords]
            ys = [p[1] for p in coords]
            maxd = ((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2) ** 0.5
        self.maxd = max(maxd, max(self.d0) if self.d0 else 0.0, 1.0)
        self.fill_weight = float(fill_weight)
        self.offset = 3.0 * self.maxd + 1.0

    def score(self, partial, action):
        c = int(action[0])
        new_route = bool(action[1])
        last = partial[2]
        if new_route or last == 0:
            return float(self.offset + (self.maxd - self.d0[c]))
        d = float(self.inst.dist(last, c))
        return float(d - self.fill_weight * self.maxd * (self.dem[c] / self.cap))


def build_component(problem, fill_weight: float = 0.2):
    return FarthestSeedNearestExtend(problem, fill_weight)
