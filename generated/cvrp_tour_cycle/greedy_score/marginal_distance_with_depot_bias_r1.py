COMPONENT = {
    "name": "marginal_distance_with_depot_bias",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "depot_bias": {"type": "float", "range": [0.0, 5.0]},
        "close_bias": {"type": "float", "range": [0.0, 10.0]},
    },
}


class MarginalDistanceWithDepotBias:
    """Score greedy para CVRP gran-tour.

    Idea:
    - Para `add`, prioriza el incremento marginal puro de distancia.
    - Además, favorece clientes "cercanos al depósito" cuando la ruta actual está vacía,
      para arrancar rutas baratas.
    - Para `close`, penaliza cerrar rutas demasiado cortas o con poca carga,
      para evitar fragmentación prematura.
    """

    def __init__(self, problem, depot_bias: float = 1.0, close_bias: float = 2.0):
        self.inst = problem.inst
        self.depot_bias = float(depot_bias)
        self.close_bias = float(close_bias)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "add":
            c = int(action[1])
            delta = float(action[2])
            depot_cost = float(self.inst.dist(0, c))
            if open_route:
                # Reduce ligeramente el peso de la distancia al depósito en rutas ya abiertas.
                return delta + self.depot_bias * 0.1 * depot_cost
            return delta + self.depot_bias * depot_cost

        if kind == "close":
            if not open_route:
                return 0.0
            load = sum(self.inst.demand[c] for c in open_route)
            route_len = len(open_route)
            # Cerrar una ruta corta/poco cargada es menos atractivo.
            slack = max(0.0, float(self.inst.capacity) - float(load))
            return self.close_bias * (1.0 / (1.0 + route_len)) + 0.05 * slack

        return 1e18


def build_component(problem, depot_bias: float = 1.0, close_bias: float = 2.0):
    return MarginalDistanceWithDepotBias(problem, depot_bias=depot_bias, close_bias=close_bias)
