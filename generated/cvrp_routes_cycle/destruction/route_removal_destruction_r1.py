from random import Random
from typing import Any

COMPONENT = {
    "name": "route_removal_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
        "bias_long_routes": {"type": "bool"},
    },
}


class RouteRemovalDestruction:
    """Libera rutas completas, priorizando rutas largas o de mayor carga."""

    def __init__(self, problem, ratio: float = 0.25, bias_long_routes: bool = True):
        self.problem = problem
        self.inst = problem.inst
        self.ratio = float(ratio)
        self.bias_long_routes = bool(bias_long_routes)

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        all_vars = set(assignment)

        routes = [tuple(r) for r in sol if r]
        if not routes:
            # fallback: liberar una variable al azar
            chosen = {rng.choice(sorted(all_vars))}
            partial = {v: val for v, val in assignment.items() if v not in chosen}
            return partial, chosen

        target = max(1, int(round(float(ratio) * len(all_vars))))

        scored = []
        for route in routes:
            length = 0.0
            prev = 0
            load = 0.0
            for c in route:
                length += self.inst.dist(prev, c)
                prev = c
                load += float(self.inst.demand[c])
            length += self.inst.dist(prev, 0)
            score = length if self.bias_long_routes else load
            scored.append((score, route))

        scored.sort(reverse=True, key=lambda t: (t[0], len(t[1]), t[1][0]))
        chosen_routes = []
        free_vars = set()

        for _, route in scored:
            route_vars = set()
            prev = 0
            for c in route:
                route_vars.add(f"x_{prev}_{c}")
                prev = c
            route_vars.add(f"x_{prev}_0")
            if len(free_vars) < target:
                chosen_routes.append(route)
                free_vars |= route_vars

        if len(free_vars) < target:
            remaining = list(all_vars - free_vars)
            rng.shuffle(remaining)
            for v in remaining:
                free_vars.add(v)
                if len(free_vars) >= target:
                    break

        free_vars &= all_vars
        if not free_vars:
            free_vars = {rng.choice(sorted(all_vars))}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, bias_long_routes: bool = True):
    return RouteRemovalDestruction(problem, ratio=ratio, bias_long_routes=bias_long_routes)
