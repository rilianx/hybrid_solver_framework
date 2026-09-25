from __future__ import annotations

from random import Random
from typing import Any

from examples.cvrp.problem_model import var_name

COMPONENT = {
    "name": "route_removal_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RouteRemovalDestruction:
    """Libera rutas completas seleccionadas, abriendo espacio para reinsertarlas desde cero."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        routes = [tuple(r) for r in sol if r]
        if not routes:
            return assignment, {next(iter(assignment))}

        k = max(1, int(round(ratio * len(routes))))
        chosen_routes = set(rng.sample(range(len(routes)), min(k, len(routes))))
        chosen_customers = {c for idx in chosen_routes for c in routes[idx]}

        free_vars = set()
        for name in assignment:
            _, a, b = name.split("_")
            i, j = int(a), int(b)
            if i in chosen_customers or j in chosen_customers:
                free_vars.add(name)

        if not free_vars:
            free_vars.add(next(iter(assignment)))
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = params.get("ratio", 0.25)
    return RouteRemovalDestruction(problem, problem.inst)
