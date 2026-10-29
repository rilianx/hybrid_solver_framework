COMPONENT = {
    "name": "best_fit_load_distance_blend",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "fill_weight": {"type": "float", "range": [0.0, 3.0]},
        "seed_far_weight": {"type": "float", "range": [0.0, 1.0]},
    },
}


class BestFitLoadDistanceBlend:
    """CVRP: idea de bin-packing. Si c cabe, el puntaje es la distancia normalizada
    (last→c) más fill_weight × la holgura que quedaría en el vehículo. Así se premian
    los clientes que completan la carga.
    Si c no cabe o la ruta está vacía, c será semilla de una ruta nueva. Esas acciones
    llevan un recargo fijo y se prefieren clientes lejanos al depósito y de demanda
    grande (difíciles de encajar después). Menor = mejor."""

    def __init__(self, problem, fill_weight=0.5, seed_far_weight=0.5):
        self.inst = problem.inst
        self.fill_weight = float(fill_weight)
        self.seed_far_weight = float(seed_far_weight)
        custs = list(self.inst.customers)
        if custs:
            self.scale = max(1e-9, sum(self.inst.dist(0, c) for c in custs) / len(custs))
            self.max_depot = max(self.inst.dist(0, c) for c in custs) / self.scale
        else:
            self.scale = 1.0
            self.max_depot = 1.0
        self.cap = max(1e-9, float(self.inst.capacity))

    def _seed_score(self, c):
        inst = self.inst
        far = inst.dist(0, c) / self.scale
        big = inst.demand[c] / self.cap
        # recargo fijo para que extender la ruta actual sea preferible a cerrarla
        base = 4.0 * (self.max_depot + 1.0) + self.fill_weight
        return base - self.seed_far_weight * far - 0.5 * big

    def score(self, partial, action):
        inst = self.inst
        c = int(action)
        current = tuple(getattr(partial, "current", ()))
        if not current:
            return float(self._seed_score(c))
        load = 0.0
        for i in current:
            load += inst.demand[i]
        new_load = load + inst.demand[c]
        if new_load <= inst.capacity:
            d = inst.dist(current[-1], c) / self.scale
            slack = (inst.capacity - new_load) / self.cap
            return float(d + self.fill_weight * slack)
        return float(self._seed_score(c) + inst.dist(current[-1], 0) / self.scale)


def build_component(problem, fill_weight: float = 0.5, seed_far_weight: float = 0.5):
    return BestFitLoadDistanceBlend(problem, fill_weight, seed_far_weight)
