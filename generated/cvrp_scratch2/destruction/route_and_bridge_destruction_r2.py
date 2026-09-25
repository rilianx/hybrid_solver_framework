from __future__ import annotations

from math import ceil
from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "route_and_bridge_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RouteAndBridgeDestruction:
    """Libera una ruta completa o un bloque contiguo de clientes, incluyendo arcos puente."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        routes = [tuple(r) for r in sol if r]
        if not routes:
            return assignment, set()

        route = rng.choice(routes)
        route_len = len(route)

        # Número de clientes a liberar, monótono con ratio.
        target = max(1, min(route_len, int(ceil(ratio * self.inst.n_customers))))

        if target >= route_len:
            block = set(route)
        else:
            start = rng.randrange(route_len)
            block = {route[(start + t) % route_len] for t in range(target)}

        free_vars: set[str] = set()
        for name in assignment:
            _, a, b = name.split("_")
            i, j = int(a), int(b)
            if i in block or j in block:
                free_vars.add(name)

        if not free_vars:
            c = route[0]
            for j in range(self.inst.n_customers + 1):
                if j != c:
                    free_vars.add(f"x_{c}_{j}")
                    free_vars.add(f"x_{j}_{c}")

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    return RouteAndBridgeDestruction(problem, problem.inst)
