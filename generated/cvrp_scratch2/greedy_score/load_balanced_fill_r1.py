from __future__ import annotations

from examples.cvrp.problem_model import CVRPInstance, InsertAction, CVRPPartial


COMPONENT = {
    "name": "load_balanced_fill",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "target_fill": {"type": "float", "range": [0.1, 1.0]},
        "open_route_penalty": {"type": "float", "range": [0.0, 20.0]},
        "slack_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class LoadBalancedFill:
    """CVRP greedy score centrado en balancear la carga de las rutas.

    Idea:
    - además del incremento de distancia, intenta llevar las rutas hacia un nivel de llenado objetivo;
    - penaliza abrir una ruta nueva si ya existen rutas con holgura útil;
    - favorece decisiones que no dejen rutas demasiado vacías ni demasiado cargadas.

    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        target_fill: float = 0.8,
        open_route_penalty: float = 3.0,
        slack_weight: float = 1.0,
    ):
        self.inst: CVRPInstance = problem.inst
        self.target_fill = float(target_fill)
        self.open_route_penalty = float(open_route_penalty)
        self.slack_weight = float(slack_weight)

    def score(self, partial: CVRPPartial, action: InsertAction) -> float:
        cap = self.inst.capacity
        demand = self.inst.demand[action.customer]
        if action.new_route:
            # Abrir una ruta nueva solo es interesante si el cliente es muy "caro" de alojar.
            return float(action.delta + self.open_route_penalty + self.slack_weight * (demand / cap))

        load_after = partial.loads[action.route] + demand
        fill_after = load_after / cap

        # Penaliza desviarse del nivel de llenado deseado.
        balance_penalty = abs(fill_after - self.target_fill)

        # Premia consumir holgura de rutas ya abiertas de forma ordenada.
        slack_after = max(0.0, 1.0 - fill_after)

        score = action.delta
        score += self.slack_weight * balance_penalty
        score += 0.25 * slack_after
        return float(score)


def build_component(
    problem,
    target_fill: float = 0.8,
    open_route_penalty: float = 3.0,
    slack_weight: float = 1.0,
):
    return LoadBalancedFill(
        problem,
        target_fill=target_fill,
        open_route_penalty=open_route_penalty,
        slack_weight=slack_weight,
    )
