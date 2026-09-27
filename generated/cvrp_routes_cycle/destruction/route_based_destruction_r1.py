from random import Random
from typing import Any

COMPONENT = {
    "name": "route_based_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.7]}},
}


class RouteBasedDestruction:
    """Libera rutas completas, priorizando las más cargadas por clientes."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        all_vars = set(assignment.keys())
        routes = [tuple(route) for route in sol if route]

        if not routes:
            free_vars = {rng.choice(tuple(all_vars))}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        route_score = []
        for idx, route in enumerate(routes):
            load = sum(float(self.inst.demand[c]) for c in route)
            route_score.append((load, len(route), idx))
        route_score.sort(reverse=True)

        target = max(1, int(round(ratio * len(all_vars))))
        chosen_routes = []
        freed = set()

        for _, _, idx in route_score:
            route = routes[idx]
            route_vars = set()
            prev = 0
            for c in route:
                route_vars.add(f"x_{prev}_{c}")
                prev = c
            route_vars.add(f"x_{prev}_0")
            if len(freed | route_vars) <= target or not freed:
                chosen_routes.append(idx)
                freed |= route_vars
            if len(freed) >= target:
                break

        if not freed:
            idx = route_score[0][2]
            route = routes[idx]
            prev = 0
            for c in route:
                freed.add(f"x_{prev}_{c}")
                prev = c
            freed.add(f"x_{prev}_0")

        if len(freed) < target:
            remaining = [v for v in all_vars if v not in freed]
            rng.shuffle(remaining)
            for v in remaining:
                freed.add(v)
                if len(freed) >= target:
                    break

        free_vars = set(freed)
        if not free_vars:
            free_vars = {rng.choice(tuple(all_vars))}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25):
    return RouteBasedDestruction(problem, problem.inst)
