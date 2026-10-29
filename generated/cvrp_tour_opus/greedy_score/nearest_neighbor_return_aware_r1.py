import math

COMPONENT = {
    "name": "nearest_neighbor_return_aware",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {"alpha": {"type": "float", "range": [0.0, 1.0]}},
}

_CLOSE_SCORE = 1e12


class NearestNeighborReturnAware:
    """Acción ("add", c, delta) o ("close", None, 0). Parcial = (built, open_route, remaining).
    Puntaje = d(último, c) + alpha * (d(c,0) - d(último,0)), normalizado. alpha=0 es vecino
    más cercano puro; alpha=1 es el costo marginal exacto de la ruta. Cerrar solo cuando no
    queda otra opción (Split reoptimiza luego los cortes del gran tour)."""

    def __init__(self, problem, alpha: float = 0.3):
        self.inst = problem.inst
        self.alpha = float(alpha)
        custs = list(self.inst.customers)
        d0 = [self.inst.dist(0, c) for c in custs]
        self.scale = (sum(d0) / len(d0)) if d0 and sum(d0) > 0 else 1.0

    def score(self, partial, action):
        kind = action[0]
        if kind != "add":
            return _CLOSE_SCORE
        c = int(action[1])
        open_route = partial[1]
        last = open_route[-1] if open_route else 0
        dist = self.inst.dist
        val = dist(last, c) + self.alpha * (dist(c, 0) - dist(last, 0))
        val = val / self.scale
        if not math.isfinite(val):
            return _CLOSE_SCORE / 2.0
        return float(val)


def build_component(problem, alpha: float = 0.3):
    return NearestNeighborReturnAware(problem, alpha)
