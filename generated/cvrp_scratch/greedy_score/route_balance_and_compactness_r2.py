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
    """CVRP: favorece un uso balanceado de la capacidad y rutas compactas,
    pero con una prioridad constructiva distinta a la inserción por delta:
    primero busca ajustar carga/llenado de la ruta y solo como desempate usa
    información geométrica local.
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
        c = int(action.customer)
        demand_c = float(inst.demand[c])
        cap = float(max(inst.capacity, 1e-9))

        # Criterio principal: ajuste de carga y uso de capacidad.
        if action.new_route:
            # Abrir ruta nueva se penaliza, pero se relaja para clientes "pesados"
            # que ayudan a no sobrecargar rutas existentes.
            demand_ratio = demand_c / cap
            return (
                self.new_route_bias
                + self.balance_weight * (0.75 - demand_ratio) ** 2
                - 0.25 * self.compactness_weight * demand_ratio
            )

        route = int(action.route)
        load = float(partial.loads[route]) if route < len(partial.loads) else 0.0
        after_load = load + demand_c
        fill = after_load / cap

        # Balance: preferir llenar rutas hacia una fracción objetivo razonable,
        # no simplemente la inserción geográficamente más corta.
        target_fill = 0.80
        balance_penalty = abs(fill - target_fill)

        # Compactness: usa la distancia de inserción solo como desempate suave,
        # normalizada para no dominar el criterio de balance.
        delta = float(action.delta)
        compactness = delta / cap

        # Ligera preferencia por rutas que ya tenían una carga consistente.
        before_fill = load / cap
        stability = abs(before_fill - target_fill)

        return (
            self.balance_weight * balance_penalty
            + 0.35 * self.balance_weight * stability
            + self.compactness_weight * compactness
        )


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
