COMPONENT = {
    "name": "route_extension_lookahead",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "lookahead_weight": {"type": "float", "range": [0.0, 5.0]},
        "end_penalty": {"type": "float", "range": [0.0, 5.0]},
    },
}


class RouteExtensionLookahead:
    """CVRP: mira no solo el coste inmediato, sino también qué tan 'aislado' queda
    el cliente elegido respecto al resto de no asignados. Penaliza abrir un extremo
    caro (cliente lejos del resto) y premia extensiones que conectan con vecinos cercanos.
    Menor puntaje = mejor."""

    def __init__(self, problem, lookahead_weight: float = 1.0, end_penalty: float = 0.5):
        self.inst = problem.inst
        self.lookahead_weight = float(lookahead_weight)
        self.end_penalty = float(end_penalty)

    def score(self, partial, action) -> float:
        inst = self.inst
        c = int(action)
        current = getattr(partial, "current", ())
        remaining = tuple(int(x) for x in getattr(partial, "remaining", ()))

        prev = int(current[-1]) if current else 0
        base = float(inst.dist(prev, c))

        # Lookahead barato: distancia del candidato a su vecino más cercano aún disponible
        # y al depósito. Si queda aislado, conviene visitarlo antes.
        best_future = float("inf")
        for other in remaining:
            if other == c:
                continue
            d = float(inst.dist(c, other))
            if d < best_future:
                best_future = d

        depot_dist = float(inst.dist(c, 0))
        if best_future == float("inf"):
            best_future = depot_dist

        # Si estamos cerrando una ruta (o sea, current no vacío), penalizamos terminar
        # con un extremo caro lejos del depósito.
        end_term = depot_dist if current else 0.0

        # Normalizamos muy suavemente para mantener determinismo y bajo coste.
        return base - self.lookahead_weight / max(best_future, 1e-9) + self.end_penalty * end_term


def build_component(problem, lookahead_weight: float = 1.0, end_penalty: float = 0.5):
    return RouteExtensionLookahead(problem, lookahead_weight=lookahead_weight, end_penalty=end_penalty)
