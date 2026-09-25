from examples.cvrp.problem_model import InsertAction, CVRPPartial


COMPONENT = {
    "name": "nearest_insertion_by_delta",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "new_route_bias": {"type": "float", "range": [0.0, 50.0]},
        "load_bias": {"type": "float", "range": [0.0, 10.0]},
    },
}


class NearestInsertionByDelta:
    """CVRP: prioriza la inserción con menor incremento de distancia.
    Añade un sesgo suave para no abrir rutas nuevas salvo que sea razonable,
    y para preferir rutas con más carga ya acumulada cuando la inserción es similar.
    Menor puntaje = mejor."""

    def __init__(self, problem, new_route_bias: float = 5.0, load_bias: float = 1.0):
        self.inst = problem.inst
        self.new_route_bias = float(new_route_bias)
        self.load_bias = float(load_bias)

    def score(self, partial: CVRPPartial, action: InsertAction) -> float:
        score = float(action.delta)
        if action.new_route:
            score += self.new_route_bias

        if action.route < len(partial.loads):
            cap = self.inst.capacity
            load = partial.loads[action.route]
            slack_after = max(0.0, cap - (load + self.inst.demand[action.customer]))
            score += self.load_bias * (slack_after / max(cap, 1e-9))
        return score


def build_component(problem, new_route_bias: float = 5.0, load_bias: float = 1.0):
    return NearestInsertionByDelta(problem, new_route_bias=new_route_bias, load_bias=load_bias)
