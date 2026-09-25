from examples.cvrp.problem_model import InsertAction, CVRPPartial


COMPONENT = {
    "name": "regret_aware_urgency",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "regret_weight": {"type": "float", "range": [0.0, 10.0]},
        "distance_weight": {"type": "float", "range": [0.0, 5.0]},
        "new_route_penalty": {"type": "float", "range": [0.0, 50.0]},
    },
}


class RegretAwareUrgency:
    """CVRP: puntuación constructiva basada en urgencia del cliente y uso de capacidad.

    La idea principal es distinta de una inserción puramente por delta:
    - prioriza clientes "urgentes" (demanda alta respecto a la capacidad),
    - favorece insertarlos en rutas con holgura limitada antes de que se saturen,
    - penaliza abrir una ruta nueva, pero sin depender solo del coste inmediato.
    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        regret_weight: float = 1.5,
        distance_weight: float = 1.0,
        new_route_penalty: float = 8.0,
    ):
        self.inst = problem.inst
        self.regret_weight = float(regret_weight)
        self.distance_weight = float(distance_weight)
        self.new_route_penalty = float(new_route_penalty)

    def score(self, partial: CVRPPartial, action: InsertAction) -> float:
        c = action.customer
        demand = float(self.inst.demand[c])
        cap = float(self.inst.capacity)
        cap = cap if cap > 0.0 else 1.0

        # Base: coste de inserción local si existe, o una aproximación de apertura de ruta.
        if action.new_route:
            # Para una ruta nueva, el cliente "consume" su propia ruta completa:
            # usar una señal de urgencia ligada a demanda y distancia al depósito.
            depot = 0
            d0 = float(self.inst.dist(depot, c))
            base = float(action.delta) + self.new_route_penalty + self.distance_weight * d0
            urgency = demand / cap
            return base - self.regret_weight * urgency

        # En una ruta existente, el criterio mira la holgura que queda tras insertar
        # y favorece meter antes los clientes más "pesados" para evitar saturación.
        route_load = float(partial.loads[action.route]) if action.route < len(partial.loads) else 0.0
        remaining_after = max(0.0, cap - route_load - demand)

        # Cuanto menos espacio quede, más urgente es esa acción.
        slack_pressure = 1.0 - (remaining_after / cap)

        # Urgencia por demanda; más demanda => más prioridad.
        urgency = demand / cap

        # Mezcla no equivalente a nearest insertion: no solo mira delta,
        # sino también la presión de capacidad de la ruta y la urgencia del cliente.
        return (
            self.distance_weight * float(action.delta)
            + self.regret_weight * urgency
            + 0.5 * slack_pressure
        )


def build_component(
    problem,
    regret_weight: float = 1.5,
    distance_weight: float = 1.0,
    new_route_penalty: float = 8.0,
):
    return RegretAwareUrgency(
        problem,
        regret_weight=regret_weight,
        distance_weight=distance_weight,
        new_route_penalty=new_route_penalty,
    )
