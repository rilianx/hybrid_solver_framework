COMPONENT = {
    "name": "capacity_packing_greedy_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "slack_weight": {"type": "float", "range": [0.0, 10.0]},
        "fill_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class CapacityPackingGreedyScore:
    """CVRP greedy score orientado a empaquetar capacidad.

    Menor puntaje es mejor. Favorece acciones que aprovechan mejor la capacidad
    residual de la ruta actual y penaliza dejar demasiada holgura.
    """

    def __init__(self, problem, distance_weight: float = 1.0, slack_weight: float = 1.5, fill_weight: float = 1.0):
        self.inst = problem.inst
        self.distance_weight = float(distance_weight)
        self.slack_weight = float(slack_weight)
        self.fill_weight = float(fill_weight)

    def _current_load(self, partial) -> float:
        current = getattr(partial, "current", ())
        inst = self.inst
        return float(sum(inst.demand[int(c)] for c in current))

    def _last_customer(self, partial):
        current = getattr(partial, "current", ())
        return int(current[-1]) if current else 0

    def score(self, partial, action) -> float:
        inst = self.inst
        c = int(action)
        last = self._last_customer(partial)

        demand = float(inst.demand[c])
        dist_term = float(inst.dist(last, c))

        load = self._current_load(partial)
        cap = float(inst.capacity)
        residual_after = max(0.0, cap - load - demand)

        # Penaliza holgura grande tras insertar c: buscamos aprovechar bien la ruta.
        slack_term = residual_after / max(cap, 1e-9)

        # Favorece llenar la ruta con demandas altas cuando hay espacio.
        fill_term = -demand / max(cap, 1e-9)

        return (
            self.distance_weight * dist_term
            + self.slack_weight * slack_term
            + self.fill_weight * fill_term
        )


def build_component(problem, distance_weight: float = 1.0, slack_weight: float = 1.5, fill_weight: float = 1.0):
    return CapacityPackingGreedyScore(
        problem,
        distance_weight=distance_weight,
        slack_weight=slack_weight,
        fill_weight=fill_weight,
    )
