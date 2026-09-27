COMPONENT = {
    "name": "demand_urgency_greedy_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "demand_weight": {"type": "float", "range": [0.0, 10.0]},
        "tail_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class DemandUrgencyGreedyScore:
    """CVRP greedy score centrado en la urgencia de demanda.

    Menor puntaje es mejor. Favorece clientes de mayor demanda (más "urgentes")
    si el coste de insertarlos no es demasiado alto.
    """

    def __init__(self, problem, distance_weight: float = 1.0, demand_weight: float = 2.0, tail_weight: float = 0.1):
        self.inst = problem.inst
        self.distance_weight = float(distance_weight)
        self.demand_weight = float(demand_weight)
        self.tail_weight = float(tail_weight)

    def _last_customer(self, partial):
        current = getattr(partial, "current", ())
        return int(current[-1]) if current else 0

    def score(self, partial, action) -> float:
        inst = self.inst
        c = int(action)
        last = self._last_customer(partial)

        demand = float(inst.demand[c])
        d = float(inst.dist(last, c))

        # Prioriza demandas grandes; el término de distancia evita elegir clientes urgentes
        # si están muy lejos del punto actual.
        urgency = -demand

        # En rutas ya iniciadas, preferimos no dejar "colas" muy caras.
        tail = float(inst.dist(c, 0))

        return self.distance_weight * d + self.demand_weight * urgency + self.tail_weight * tail


def build_component(problem, distance_weight: float = 1.0, demand_weight: float = 2.0, tail_weight: float = 0.1):
    return DemandUrgencyGreedyScore(
        problem,
        distance_weight=distance_weight,
        demand_weight=demand_weight,
        tail_weight=tail_weight,
    )
