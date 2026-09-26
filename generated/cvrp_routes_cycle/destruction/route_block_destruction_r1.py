from random import Random
from typing import Any

COMPONENT = {
    "name": "route_block_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class RouteBlockDestruction:
    """Libera rutas completas, favoreciendo una gran ruptura estructural del tour."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        routes = list(sol)
        if not routes:
            free_vars = set()
            if assignment:
                key = next(iter(assignment))
                free_vars = {key}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        n_customers = self.inst.n_customers
        target = max(1, int(round(ratio * n_customers)))

        route_info = []
        for route in routes:
            edges = []
            prev = 0
            for c in route:
                edges.append(f"x_{prev}_{c}")
                prev = c
            edges.append(f"x_{prev}_0")
            route_info.append((len(route), edges))

        order = list(range(len(routes)))
        rng.shuffle(order)
        order.sort(key=lambda idx: route_info[idx][0], reverse=True)

        free_vars: set[str] = set()
        freed_customers = 0
        for idx in order:
            if freed_customers >= target and free_vars:
                break
            _, edges = route_info[idx]
            for v in edges:
                free_vars.add(v)
            freed_customers += len(routes[idx])

        if not free_vars:
            _, edges = min(route_info, key=lambda t: t[0])
            free_vars.update(edges)

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = float(params.get("ratio", 0.35))
    return RouteBlockDestruction(problem)
