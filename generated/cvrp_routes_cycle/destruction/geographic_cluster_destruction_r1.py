from random import Random
from typing import Any
import math

COMPONENT = {
    "name": "geographic_cluster_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class GeographicClusterDestruction:
    """Libera una nube espacial de clientes cercanos a un cliente semilla."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _coords(self, c: int):
        return self.inst.coords[c]

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        all_vars = set(assignment.keys())
        customers = list(self.inst.customers)

        if not customers:
            free_vars = {rng.choice(tuple(all_vars))}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        seed = rng.choice(customers)
        sx, sy = self._coords(seed)

        scored = []
        for c in customers:
            x, y = self._coords(c)
            d = math.hypot(float(x) - float(sx), float(y) - float(sy))
            scored.append((d, c))
        scored.sort()

        target_customers = max(1, int(round(ratio * len(customers))))
        chosen_customers = {c for _, c in scored[:target_customers]}

        free_vars = set()
        for route in sol:
            prev = 0
            for c in route:
                if c in chosen_customers:
                    free_vars.add(f"x_{prev}_{c}")
                    if prev != 0:
                        free_vars.add(f"x_{prev}_{c}")
                    prev = c
                else:
                    prev = c
            if route:
                last = route[-1]
                if any(c in chosen_customers for c in route):
                    free_vars.add(f"x_{last}_0")

        for route in sol:
            prev = 0
            for c in route:
                if c in chosen_customers:
                    free_vars.add(f"x_{prev}_{c}")
                prev = c
            if route and any(c in chosen_customers for c in route):
                free_vars.add(f"x_{prev}_0")

        if not free_vars:
            free_vars = {rng.choice(tuple(all_vars))}

        # Ensure a bit more freedom if the selected customers are isolated.
        if len(free_vars) < max(1, int(round(ratio * len(all_vars)))):
            remaining = [v for v in all_vars if v not in free_vars]
            rng.shuffle(remaining)
            for v in remaining:
                free_vars.add(v)
                if len(free_vars) >= max(1, int(round(ratio * len(all_vars)))):
                    break

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return GeographicClusterDestruction(problem, problem.inst)
