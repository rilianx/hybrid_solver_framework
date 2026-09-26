COMPONENT = {
    "name": "route_save_ratio_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "join_weight": {"type": "float", "range": [0.0, 5.0]},
        "opening_penalty": {"type": "float", "range": [0.0, 5.0]},
    },
}


class RouteSaveRatioScore:
    """CVRP greedy score: estima el ahorro local de añadir el cliente `action` a la
    ruta actual comparado con dejarlo como inicio de una ruta nueva. Favorece insertar
    clientes que 'ahorran' más distancia respecto a cerrar y reabrir rutas. Menor
    puntaje = mejor."""

    def __init__(self, problem, join_weight: float = 1.0, opening_penalty: float = 0.2):
        self.inst = problem.inst
        self.join_weight = float(join_weight)
        self.opening_penalty = float(opening_penalty)

    def score(self, partial, action):
        inst = self.inst
        c = int(action)

        if getattr(partial, "current", ()):
            last = int(partial.current[-1])
            route_has_prefix = True
        else:
            last = 0
            route_has_prefix = False

        # Local "savings" proxy:
        # cost of appending to current route vs. starting a fresh route.
        append_cost = float(inst.dist(last, c)) + float(inst.dist(c, 0)) - float(inst.dist(last, 0))
        fresh_cost = float(inst.dist(0, c)) + float(inst.dist(c, 0))

        # Prefer actions that reduce the need to start new routes and that fit well
        # into the current route tail.
        join_benefit = fresh_cost - append_cost
        opening = 0.0 if route_has_prefix else self.opening_penalty * float(inst.dist(0, c))

        # Smaller score is better: more benefit => lower score.
        return opening - self.join_weight * join_benefit


def build_component(problem, join_weight: float = 1.0, opening_penalty: float = 0.2):
    return RouteSaveRatioScore(problem, join_weight=join_weight, opening_penalty=opening_penalty)
