COMPONENT = {
    "name": "nearest_neighbor_distance",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {"route_bias": {"type": "float", "range": [0.0, 5.0]}},
}


class NearestNeighborDistance:
    """CVRP: puntúa por cercanía al último cliente de la ruta actual.
    Si no hay ruta abierta, usa el depósito como referencia.
    Menor puntaje = mejor."""

    def __init__(self, problem, route_bias: float = 1.0):
        self.inst = problem.inst
        self.route_bias = float(route_bias)

    def score(self, partial, action) -> float:
        inst = self.inst
        c = int(action)
        current = getattr(partial, "current", ())
        prev = int(current[-1]) if current else 0

        # Distancia incremental principal
        dist_prev = float(inst.dist(prev, c))

        # Ligera preferencia por cerrar rutas "limpias" si la demanda del cliente es alta:
        # clientes grandes suelen ser más restrictivos, así que acercarlos antes ayuda.
        demand = float(inst.demand[c])
        capacity = max(float(inst.capacity), 1e-9)
        urgency = demand / capacity

        return dist_prev - self.route_bias * urgency


def build_component(problem, route_bias: float = 1.0):
    return NearestNeighborDistance(problem, route_bias=route_bias)
