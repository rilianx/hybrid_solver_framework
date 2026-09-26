COMPONENT = {
    "name": "lookahead_balance_and_radius",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "radius_weight": {"type": "float", "range": [0.0, 10.0]},
        "balance_weight": {"type": "float", "range": [0.0, 10.0]},
        "close_weight": {"type": "float", "range": [0.0, 1000.0]},
    },
}


class LookaheadBalanceAndRadius:
    """CVRP tour: usa una mirada local de un paso para preferir clientes que mantengan
    compacta la ruta y, al mismo tiempo, balanceen la demanda acumulada respecto a la capacidad.
    También puede cerrar la ruta cuando eso resulta consistente con la holgura restante.
    Menor puntaje = mejor."""

    def __init__(self, problem, radius_weight: float = 1.0, balance_weight: float = 1.0, close_weight: float = 5.0):
        self.inst = problem.inst
        self.radius_weight = float(radius_weight)
        self.balance_weight = float(balance_weight)
        self.close_weight = float(close_weight)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]
        cap = float(self.inst.capacity)

        if kind == "close":
            if not open_route:
                return 0.0
            load = sum(self.inst.demand[c] for c in open_route)
            slack = max(0.0, cap - load)
            # Close when the remaining slack is small.
            return self.close_weight * (slack / max(cap, 1e-9))

        c = int(action[1])
        demand = float(self.inst.demand[c])

        # Radial compactness: prefer clients closer to the depot as route starters,
        # and closer to the current tail as extensions.
        if not open_route:
            radius = self.inst.dist(0, c)
            load_after = demand
            balance = abs((load_after / max(cap, 1e-9)) - 0.5)
            return self.radius_weight * radius + self.balance_weight * balance

        last = open_route[-1]
        append_cost = self.inst.dist(last, c) + self.inst.dist(c, 0) - self.inst.dist(last, 0)
        load_before = sum(self.inst.demand[x] for x in open_route)
        load_after = load_before + demand
        slack_after = max(0.0, cap - load_after)

        # Balance term prefers using capacity smoothly without overshooting.
        balance = abs((load_after / max(cap, 1e-9)) - 0.7)
        # Lookahead proxy: reward actions that keep the tail close to remaining customers' region
        # by penalizing large append cost and also penalizing excessive leftover slack.
        return self.radius_weight * append_cost + self.balance_weight * (balance + slack_after / max(cap, 1e-9))


def build_component(problem, radius_weight: float = 1.0, balance_weight: float = 1.0, close_weight: float = 5.0):
    return LookaheadBalanceAndRadius(problem, radius_weight=radius_weight, balance_weight=balance_weight, close_weight=close_weight)
