COMPONENT = {
    "name": "nearest_extension_with_close_penalty",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "close_penalty": {"type": "float", "range": [0.0, 1000.0]},
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "return_bias": {"type": "float", "range": [0.0, 10.0]},
    },
}


class NearestExtensionWithClosePenalty:
    """CVRP tour: prioriza extender la ruta abierta con el cliente más cercano al último nodo
    de la ruta. Cerrar la ruta tiene una penalización fija para evitar cortes prematuros.
    Menor puntaje = mejor."""

    def __init__(self, problem, close_penalty: float = 10.0, distance_weight: float = 1.0, return_bias: float = 0.0):
        self.inst = problem.inst
        self.close_penalty = float(close_penalty)
        self.distance_weight = float(distance_weight)
        self.return_bias = float(return_bias)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "close":
            # Encourage keeping routes a bit longer unless extending is clearly bad.
            return self.close_penalty + self.return_bias * (1.0 if open_route else 0.0)

        c = int(action[1])
        d = self.inst.demand[c]

        if not open_route:
            # Starting a new route: prefer customers close to the depot.
            return self.distance_weight * (self.inst.dist(0, c) + self.return_bias * d)

        last = open_route[-1]
        delta = self.inst.dist(last, c) + self.inst.dist(c, 0) - self.inst.dist(last, 0)
        return self.distance_weight * delta + self.return_bias * d


def build_component(problem, close_penalty: float = 10.0, distance_weight: float = 1.0, return_bias: float = 0.0):
    return NearestExtensionWithClosePenalty(problem, close_penalty=close_penalty, distance_weight=distance_weight, return_bias=return_bias)
