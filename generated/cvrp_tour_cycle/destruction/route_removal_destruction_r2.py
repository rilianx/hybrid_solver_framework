from __future__ import annotations

from random import Random
from typing import Any


COMPONENT = {
    "name": "route_removal_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.from_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RouteRemovalDestruction:
    """Libera clientes dispersos a lo largo del gran tour, guiado por la estructura de posiciones."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def _tour_from_assignment(self, assignment: dict[str, float]) -> list[int]:
        succ: dict[int, int] = {}
        pred: dict[int, int] = {}

        for v, val in assignment.items():
            if not v.startswith("x_") or val <= 0.5:
                continue
            try:
                _, a, b = v.split("_")
                i, j = int(a), int(b)
            except Exception:
                continue
            succ[i] = j
            pred[j] = i

        # Follow the tour from the depot if possible.
        tour: list[int] = []
        cur = succ.get(0, None)
        seen: set[int] = set()
        while cur is not None and cur != 0 and cur not in seen:
            tour.append(cur)
            seen.add(cur)
            cur = succ.get(cur, None)

        if tour:
            return tour

        # Fallback: reconstruct from predecessor chain if needed.
        starts = [i for i in succ.keys() if i != 0 and i not in pred]
        if starts:
            cur = starts[0]
            while cur != 0 and cur not in seen:
                tour.append(cur)
                seen.add(cur)
                cur = succ.get(cur, 0)
            if tour:
                return tour

        # Last resort: any customer appearing in assignment order.
        customers = []
        for c in getattr(self.inst, "customers", []):
            customers.append(c)
        return customers

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        vars_all = set(assignment.keys())

        tour = self._tour_from_assignment(assignment)
        n = len(tour)
        if n == 0:
            free_vars = set()
            if vars_all:
                free_vars = {next(iter(vars_all))}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        target = max(1, int(round(ratio * n)))
        target = min(target, n)

        # Disperse removals along the tour instead of taking one contiguous block.
        # We pick a random step co-prime-ish with the tour length to spread the freed customers.
        if n == 1:
            chosen_customers = {tour[0]}
        else:
            step = rng.randint(1, max(1, n - 1))
            # Make the stride less likely to create a short cycle by avoiding even steps on even n.
            if n % 2 == 0 and step % 2 == 0:
                step = step + 1 if step < n - 1 else step - 1
            start = rng.randrange(n)
            chosen_customers: set[int] = set()
            pos = start
            while len(chosen_customers) < target:
                chosen_customers.add(tour[pos])
                pos = (pos + step) % n

        free_vars = set()
        for v in vars_all:
            if not v.startswith("x_"):
                continue
            try:
                _, a, b = v.split("_")
                i, j = int(a), int(b)
            except Exception:
                continue
            if i in chosen_customers or j in chosen_customers:
                free_vars.add(v)

        if not free_vars and vars_all:
            free_vars.add(next(iter(vars_all)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return RouteRemovalDestruction(problem)
