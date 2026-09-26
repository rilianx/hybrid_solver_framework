from random import Random
from typing import Any


COMPONENT = {
    "name": "arc_cut_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class ArcCutDestruction:
    """Libera una ruta completa o un bloque de ruta y sus arcos incidentes."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    @staticmethod
    def _x(i: int, j: int) -> str:
        return f"x_{i}_{j}"

    def _customers_from_solution(self, sol) -> list[list[int]]:
        routes: list[list[int]] = []
        if isinstance(sol, tuple) or isinstance(sol, list):
            for route in sol:
                if isinstance(route, tuple) or isinstance(route, list):
                    custs = [int(c) for c in route if int(c) != 0]
                    if custs:
                        routes.append(custs)
        return routes

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        customers = self._customers_from_solution(sol)

        if customers:
            route = rng.choice(customers)
            target = max(1, int(round(ratio * len(route))))
            if target >= len(route):
                subset = set(route)
            else:
                start = rng.randrange(len(route))
                subset = set()
                for k in range(target):
                    subset.add(route[(start + k) % len(route)])
        else:
            all_customers = list(getattr(self.inst, "customers", []))
            if not all_customers:
                free_vars = set()
                partial = dict(assignment)
                return partial, free_vars
            seed = rng.choice(all_customers)
            subset = {seed}
            target = max(1, int(round(ratio * len(all_customers))))
            shuffled = [c for c in all_customers if c != seed]
            rng.shuffle(shuffled)
            for c in shuffled:
                if len(subset) >= target:
                    break
                subset.add(c)

        subset_set = set(subset)
        free_vars: set[str] = set()

        # Free all arcs incident to the selected customers.
        for i in subset_set:
            for j in range(self.inst.n_customers + 1):
                if j != i:
                    free_vars.add(self._x(i, j))
                    free_vars.add(self._x(j, i))

        # Also free route-entry/route-exit arcs crossing the cut when available.
        for i in range(self.inst.n_customers + 1):
            for j in subset_set:
                if i != j:
                    free_vars.add(self._x(i, j))
                    free_vars.add(self._x(j, i))

        # Keep only variables present in the assignment.
        free_vars = {v for v in free_vars if v in assignment}

        if not free_vars:
            key = next(iter(assignment))
            free_vars = {key}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    return ArcCutDestruction(problem)
