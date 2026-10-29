COMPONENT = {
    "name": "nearest_neighbor_closure_penalty",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "return_weight": {"type": "float", "range": [0.0, 1.0]},
        "reopen_penalty": {"type": "float", "range": [0.0, 5.0]},
    },
}


class NearestNeighborClosurePenalty:
    """CVRP: la acción es un cliente c. Si c cabe en la ruta actual, el puntaje es la
    distancia desde el último cliente más una fracción del regreso al depósito.
    Si no cabe (la acción cierra la ruta), el costo es volver al depósito y salir hacia c,
    más una penalización proporcional a la distancia media al depósito. Menor = mejor."""

    def __init__(self, problem, return_weight=0.0, reopen_penalty=1.0):
        self.inst = problem.inst
        self.return_weight = float(return_weight)
        self.reopen_penalty = float(reopen_penalty)
        custs = list(self.inst.customers)
        if custs:
            self.mean_depot = sum(self.inst.dist(0, c) for c in custs) / len(custs)
        else:
            self.mean_depot = 1.0

    def score(self, partial, action):
        inst = self.inst
        c = int(action)
        current = tuple(getattr(partial, "current", ()))
        if not current:
            return float(inst.dist(0, c) + self.return_weight * inst.dist(c, 0))
        last = current[-1]
        load = 0.0
        for i in current:
            load += inst.demand[i]
        if load + inst.demand[c] <= inst.capacity:
            return float(inst.dist(last, c) + self.return_weight * inst.dist(c, 0))
        # cierra la ruta actual y abre una nueva en c
        return float(inst.dist(last, 0) + inst.dist(0, c)
                     + self.return_weight * inst.dist(c, 0)
                     + self.reopen_penalty * self.mean_depot)


def build_component(problem, return_weight: float = 0.0, reopen_penalty: float = 1.0):
    return NearestNeighborClosurePenalty(problem, return_weight, reopen_penalty)
