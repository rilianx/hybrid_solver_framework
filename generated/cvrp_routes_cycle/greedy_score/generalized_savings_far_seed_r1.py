COMPONENT = {
    "name": "generalized_savings_far_seed",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "shape_lambda": {"type": "float", "range": [0.5, 2.0]},
        "seed_weight": {"type": "float", "range": [0.0, 1.0]},
    },
}


class GeneralizedSavingsFarSeed:
    """CVRP: si c cabe en la ruta actual, el puntaje es menos el ahorro generalizado.
    El ahorro es s = d(last,0) + d(0,c) − λ·d(last,c): conviene encadenar clientes que,
    servidos por separado, costarían mucho ir y volver.
    Si la ruta está vacía o c no cabe, c será semilla. La semilla lleva un desplazamiento
    que la hace siempre peor que extender, y se prefieren los clientes más lejanos al
    depósito (barrido desde la periferia). Menor = mejor."""

    def __init__(self, problem, shape_lambda=1.0, seed_weight=1.0):
        self.inst = problem.inst
        self.lam = float(shape_lambda)
        self.seed_weight = float(seed_weight)
        custs = list(self.inst.customers)
        maxd = max((self.inst.dist(0, c) for c in custs), default=1.0)
        self.maxd = max(1e-9, float(maxd))
        # cota superior de cualquier puntaje de extensión: λ·d(last,c) ≤ λ·2·maxd
        self.offset = (2.0 * self.lam + 2.0) * self.maxd + 1.0

    def _seed(self, c):
        return self.offset - self.seed_weight * self.inst.dist(0, c)

    def score(self, partial, action):
        inst = self.inst
        c = int(action)
        current = tuple(getattr(partial, "current", ()))
        if not current:
            return float(self._seed(c))
        last = current[-1]
        load = 0.0
        for i in current:
            load += inst.demand[i]
        if load + inst.demand[c] <= inst.capacity:
            s = inst.dist(last, 0) + inst.dist(0, c) - self.lam * inst.dist(last, c)
            return float(-s)
        return float(self._seed(c) + inst.dist(last, 0))


def build_component(problem, shape_lambda: float = 1.0, seed_weight: float = 1.0):
    return GeneralizedSavingsFarSeed(problem, shape_lambda, seed_weight)
