from examples.cvrp.problem_model import InsertAction, CVRPPartial


COMPONENT = {
    "name": "route_balance_and_compactness",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "balance_weight": {"type": "float", "range": [0.0, 10.0]},
        "compactness_weight": {"type": "float", "range": [0.0, 10.0]},
        "new_route_bias": {"type": "float", "range": [0.0, 20.0]},
    },
}


class RouteBalanceAndCompactness:
    """CVRP: favorece rutas compactas y balanceadas en carga.
    No solo mira el incremento directo: premia insertar en rutas ya densas y penaliza
    rutas muy desbalanceadas o abrir nuevas rutas cuando no hace falta.
    Menor puntaje = mejor."""

    def __init__(
        self,
        problem,
        balance_weight: float = 1.0,
        compactness_weight: float = 1.0,
        new_route_bias: float = 4.0,
    ):
        self.inst = problem.inst
        self.balance_weight = float(balance_weight)
        self.compactness_weight = float(compactness_weight)
        self.new_route_bias = float(new_route_bias)

    def score(self, partial: CVRPPartial, action: InsertAction) -> float:
        inst = self.inst
        c = action.customer
        d = float(action.delta)

        if action.new_route:
            # Abrir ruta nueva es aceptable, pero se evita si el cliente puede encajar bien.
            return d + self.new_route_bias + self.balance_weight * (inst.demand[c] / max(inst.capacity, 1e-9))

        route = action.route
        load = partial.loads[route] if route < len(partial.loads) else 0.0
        after_load = load + inst.demand[c]
        cap = inst.capacity

        # Balance: penaliza rutas que queden muy vacías o muy cargadas.
        fill = after_load / max(cap, 1e-9)
        balance_penalty = abs(fill - 0.5)

        # Compactness: preferir inserciones baratas en rutas ya establecidas.
        compactness = d / max(cap, 1e-9)

        return d + self.balance_weight * balance_penalty + self.compactness_weight * compactness


def build_component(
    problem,
    balance_weight: float = 1.0,
    compactness_weight: float = 1.0,
    new_route_bias: float = 4.0,
):
    return RouteBalanceAndCompactness(
        problem,
        balance_weight=balance_weight,
        compactness_weight=compactness_weight,
        new_route_bias=new_route_bias,
    )
