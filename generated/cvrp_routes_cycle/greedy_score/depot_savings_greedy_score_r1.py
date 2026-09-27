COMPONENT = {
    "name": "depot_savings_greedy_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "savings_weight": {"type": "float", "range": [0.0, 5.0]},
        "depot_bias": {"type": "float", "range": [0.0, 5.0]},
    },
}


class DepotSavingsGreedyScore:
    """CVRP greedy score basado en ahorro tipo Clarke-Wright.

    Menor puntaje es mejor. Prefiere extensiones que añaden poca distancia extra
    respecto a volver al depósito: si la acción mantiene la ruta compacta, puntúa mejor.
    """

    def __init__(self, problem, savings_weight: float = 1.0, depot_bias: float = 0.2):
        self.inst = problem.inst
        self.savings_weight = float(savings_weight)
        self.depot_bias = float(depot_bias)

    def _last_customer(self, partial):
        current = getattr(partial, "current", ())
        return int(current[-1]) if current else 0

    def score(self, partial, action) -> float:
        inst = self.inst
        c = int(action)
        last = self._last_customer(partial)

        d_last_c = float(inst.dist(last, c))
        d_c_depot = float(inst.dist(c, 0))
        d_last_depot = float(inst.dist(last, 0))

        # Ahorro clásico: cuánto peor es ir a c antes de cerrar la ruta
        savings = d_last_c + d_c_depot - d_last_depot

        # Sesgo suave hacia clientes más cercanos al depósito cuando no hay contexto previo
        depot_term = d_c_depot

        return self.savings_weight * savings + self.depot_bias * depot_term


def build_component(problem, savings_weight: float = 1.0, depot_bias: float = 0.2):
    return DepotSavingsGreedyScore(problem, savings_weight=savings_weight, depot_bias=depot_bias)
