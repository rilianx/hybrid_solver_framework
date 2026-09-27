COMPONENT = {
    "name": "future_regret_lookahead",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "regret_weight": {"type": "float", "range": [0.0, 20.0]},
        "distance_weight": {"type": "float", "range": [0.0, 5.0]},
        "balance_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class FutureRegretLookahead:
    """Score con sesgo de 'regret' local usando solo información barata.

    Idea:
    - Prefiere acciones que no solo son buenas ahora, sino que dejan buenas opciones
      para los clientes restantes.
    - Si hay muchos clientes restantes, penaliza elegir uno que sea claramente peor
      que el mejor candidato disponible.
    - Usa una medida simple de cercanía al mejor candidato restante (sin buscar optimalidad).
    """

    def __init__(self, problem, regret_weight: float = 2.0, distance_weight: float = 1.0, balance_weight: float = 0.5):
        self.inst = problem.inst
        self.regret_weight = float(regret_weight)
        self.distance_weight = float(distance_weight)
        self.balance_weight = float(balance_weight)

    def _min_remaining_depot_dist(self, remaining) -> float:
        if not remaining:
            return 0.0
        best = None
        for c in remaining:
            d = float(self.inst.dist(0, int(c)))
            if best is None or d < best:
                best = d
        return 0.0 if best is None else best

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "add":
            c = int(action[1])
            delta = float(action[2])
            depot_d = float(self.inst.dist(0, c))
            min_dep_remaining = self._min_remaining_depot_dist(remaining)

            # Regret simple: si el cliente elegido está lejos del "mejor" restante,
            # su prioridad baja.
            regret = max(0.0, depot_d - min_dep_remaining)

            # Balance: si la ruta está vacía, preferimos no arrancar con clientes extremadamente lejanos.
            route_balance = 0.0
            if not open_route:
                route_balance = depot_d

            return (
                self.distance_weight * delta
                + self.regret_weight * regret
                + self.balance_weight * route_balance
            )

        if kind == "close":
            if not open_route:
                return 0.0

            load = sum(self.inst.demand[c] for c in open_route)
            cap = float(self.inst.capacity)
            fill = load / cap if cap > 0 else 0.0
            # Cerrar es preferible cuando la ruta ya tiene una carga razonable.
            # Si quedan muchos clientes, ser conservador y no cerrar demasiado pronto.
            rem_factor = 1.0 / (1.0 + len(remaining))
            return 1.5 * (1.0 - fill) + rem_factor

        return 1e18


def build_component(problem, regret_weight: float = 2.0, distance_weight: float = 1.0, balance_weight: float = 0.5):
    return FutureRegretLookahead(
        problem,
        regret_weight=regret_weight,
        distance_weight=distance_weight,
        balance_weight=balance_weight,
    )
