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
    """CVRP: combina coste inmediato y urgencia implícita.
    La idea es favorecer acciones que no 'hipotequen' demasiado al cliente:
    inserciones baratas en sí mismas, pero penalizando especialmente abrir una ruta nueva
    y dejando al cliente con pocas alternativas buenas (aproximado por el incremento).
    Menor puntaje = mejor."""

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
        d = float(action.delta)
        c = action.customer
        demand = self.inst.demand[c]
        cap = self.inst.capacity

        if action.new_route:
            base = d + self.new_route_penalty
            # Más castigo si el cliente tiene mucha demanda respecto a la capacidad.
            return base + self.regret_weight * (demand / max(cap, 1e-9))

        route_load = partial.loads[action.route] if action.route < len(partial.loads) else 0.0
        residual = max(0.0, cap - route_load - demand)

        # Urgencia: clientes que dejan poca holgura después de insertarlos.
        urgency = demand / max(cap, 1e-9)

        # El incremento manda, pero la urgencia y la holgura inclinan el orden.
        return self.distance_weight * d + self.regret_weight * urgency + (residual / max(cap, 1e-9))


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
