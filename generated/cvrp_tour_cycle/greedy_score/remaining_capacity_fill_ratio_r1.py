COMPONENT = {
    "name": "remaining_capacity_fill_ratio",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "fill_weight": {"type": "float", "range": [0.0, 10.0]},
        "slack_weight": {"type": "float", "range": [0.0, 10.0]},
        "route_opening_bonus": {"type": "float", "range": [0.0, 5.0]},
    },
}


class RemainingCapacityFillRatio:
    """Score orientado a empaquetar rutas densas.

    Idea:
    - Prefiere añadir clientes que aprovechan bien la capacidad restante.
    - Penaliza dejar mucha holgura tras el añadido.
    - Favorece comenzar rutas cuando el cliente encaja muy bien en una ruta nueva.
    """

    def __init__(self, problem, fill_weight: float = 3.0, slack_weight: float = 1.0, route_opening_bonus: float = 0.5):
        self.inst = problem.inst
        self.fill_weight = float(fill_weight)
        self.slack_weight = float(slack_weight)
        self.route_opening_bonus = float(route_opening_bonus)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "add":
            c = int(action[1])
            d = float(self.inst.demand[c])
            cap = float(self.inst.capacity)
            used = sum(self.inst.demand[x] for x in open_route)
            new_used = used + d
            fill_ratio = new_used / cap if cap > 0 else 0.0
            slack = cap - new_used
            if not open_route:
                # Abrir ruta con clientes "grandes" suele ser más útil.
                return -self.route_opening_bonus * fill_ratio + self.slack_weight * (slack / max(cap, 1.0))
            return -self.fill_weight * fill_ratio + self.slack_weight * (slack / max(cap, 1.0))

        if kind == "close":
            if not open_route:
                return 0.0
            load = sum(self.inst.demand[c] for c in open_route)
            cap = float(self.inst.capacity)
            fill_ratio = load / cap if cap > 0 else 0.0
            # Cerrar es mejor cuando la ruta quedó bien rellena.
            return 1.0 - self.fill_weight * fill_ratio

        return 1e18


def build_component(problem, fill_weight: float = 3.0, slack_weight: float = 1.0, route_opening_bonus: float = 0.5):
    return RemainingCapacityFillRatio(
        problem,
        fill_weight=fill_weight,
        slack_weight=slack_weight,
        route_opening_bonus=route_opening_bonus,
    )
