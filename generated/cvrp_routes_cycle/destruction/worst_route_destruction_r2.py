from __future__ import annotations

from random import Random
from typing import Any

from generated.cvrp_routes_cycle.model.parts import canonical


COMPONENT = {
    "name": "worst_route_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.9]}},
}


class WorstRouteDestruction:
    """Libera la totalidad de una o varias rutas con mayor contribución a distancia."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _route_cost(self, route) -> float:
        prev = 0
        cost = 0.0
        for c in route:
            cost += float(self.inst.dist(prev, c))
            prev = c
        cost += float(self.inst.dist(prev, 0))
        return cost

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        sol = canonical(sol)
        assignment = self.problem.to_assignment(sol)

        routes = list(sol)
        if not routes:
            free_vars = {next(iter(assignment))}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        scored = sorted(
            ((self._route_cost(route), idx, route) for idx, route in enumerate(routes)),
            reverse=True,
        )

        target = max(1, min(len(routes), int(round(ratio * len(routes)))))
        chosen_routes = [route for _, _, route in scored[:target]]

        free_vars: set[str] = set()
        for route in chosen_routes:
            free_vars.update(self._route_arc_vars(route))

        # Si por algún motivo no existen esas variables en la asignación,
        # liberar toda la estructura asociada a la peor ruta encontrada.
        if not free_vars:
            _, _, route = scored[0]
            free_vars.update(self._route_arc_vars(route))

        free_vars = {v for v in free_vars if v in assignment}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars

    def _route_arc_vars(self, route) -> set[str]:
        free_vars: set[str] = set()
        if not route:
            return free_vars

        # Arcos del recorrido completo: depósito -> primer cliente -> ... -> último cliente -> depósito
        nodes = [0, *route, 0]
        for i, j in zip(nodes, nodes[1:]):
            free_vars.add(f"x_{i}_{j}")
        return free_vars


def build_component(problem, ratio: float = 0.3):
    return WorstRouteDestruction(problem, problem.inst)
