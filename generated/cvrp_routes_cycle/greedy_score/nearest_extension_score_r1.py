COMPONENT = {
    "name": "nearest_extension_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "distance_weight": {"type": "float", "range": [0.0, 5.0]},
        "depot_bias": {"type": "float", "range": [0.0, 5.0]},
    },
}


class NearestExtensionScore:
    """CVRP greedy score: favorece extender la ruta actual al cliente más cercano
    al último nodo visitado, con una ligera preferencia por no alejarse demasiado del
    depósito cuando la ruta está empezando. Menor puntaje = mejor."""

    def __init__(self, problem, distance_weight: float = 1.0, depot_bias: float = 0.2):
        self.inst = problem.inst
        self.distance_weight = float(distance_weight)
        self.depot_bias = float(depot_bias)

    def score(self, partial, action):
        inst = self.inst
        c = int(action)

        if getattr(partial, "current", ()):
            last = int(partial.current[-1])
            route_len = len(partial.current)
        else:
            last = 0
            route_len = 0

        to_last = float(inst.dist(last, c))
        to_depot = float(inst.dist(0, c))

        # A route that is just starting should favor nodes not too far from depot;
        # once inside a route, closeness to the current end dominates.
        start_penalty = self.depot_bias * to_depot / (1.0 + route_len)
        return self.distance_weight * to_last + start_penalty


def build_component(problem, distance_weight: float = 1.0, depot_bias: float = 0.2):
    return NearestExtensionScore(problem, distance_weight=distance_weight, depot_bias=depot_bias)
