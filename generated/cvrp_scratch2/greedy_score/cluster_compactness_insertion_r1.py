from __future__ import annotations

import math

from examples.cvrp.problem_model import CVRPInstance, InsertAction, CVRPPartial


COMPONENT = {
    "name": "cluster_compactness_insertion",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "compactness_weight": {"type": "float", "range": [0.0, 5.0]},
        "endpoints_weight": {"type": "float", "range": [0.0, 5.0]},
        "new_route_penalty": {"type": "float", "range": [0.0, 20.0]},
    },
}


class ClusterCompactnessInsertion:
    """CVRP greedy score que favorece mantener rutas compactas y coherentes geométricamente.

    Idea:
    - el incremento real (`action.delta`) sigue siendo la base;
    - penaliza inserciones que "estiran" una ruta entre vecinos lejanos;
    - premia insertar un cliente cerca de su predecesor y sucesor de ruta;
    - penaliza abrir ruta nueva salvo cuando compensa por compacidad.

    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        compactness_weight: float = 1.0,
        endpoints_weight: float = 0.5,
        new_route_penalty: float = 2.0,
    ):
        self.inst: CVRPInstance = problem.inst
        self.compactness_weight = float(compactness_weight)
        self.endpoints_weight = float(endpoints_weight)
        self.new_route_penalty = float(new_route_penalty)

    def score(self, partial: CVRPPartial, action: InsertAction) -> float:
        c = action.customer
        if action.new_route:
            # Una ruta nueva es compacta por definición, pero cuesta "romper" la mezcla.
            return float(action.delta + self.new_route_penalty)

        route = partial.routes[action.route]
        prev = 0 if action.pos == 0 else route[action.pos - 1]
        nxt = 0 if action.pos == len(route) else route[action.pos]

        d_prev_c = self.inst.dist(prev, c)
        d_c_next = self.inst.dist(c, nxt)
        d_prev_next = self.inst.dist(prev, nxt)

        # Coste de "estiramiento": si el cliente encaja mal entre sus vecinos, sube el score.
        stretch = (d_prev_c + d_c_next) - d_prev_next

        # Endpoints: evitar que el cliente quede lejos de ambos extremos de la ruta.
        first = route[0]
        last = route[-1]
        endpoint_pressure = min(self.inst.dist(c, first), self.inst.dist(c, last))

        score = action.delta
        score += self.compactness_weight * stretch
        score += self.endpoints_weight * 0.1 * endpoint_pressure
        return float(score)


def build_component(
    problem,
    compactness_weight: float = 1.0,
    endpoints_weight: float = 0.5,
    new_route_penalty: float = 2.0,
):
    return ClusterCompactnessInsertion(
        problem,
        compactness_weight=compactness_weight,
        endpoints_weight=endpoints_weight,
        new_route_penalty=new_route_penalty,
    )
