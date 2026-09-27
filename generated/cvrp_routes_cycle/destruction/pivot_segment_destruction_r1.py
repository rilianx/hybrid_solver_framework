from random import Random
from typing import Any

COMPONENT = {
    "name": "pivot_segment_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.7]}},
}


class PivotSegmentDestruction:
    """Libera un segmento contiguo dentro de una ruta, anclado en un pivote aleatorio."""

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

        route = rng.choice(routes)
        m = len(route)
        if m == 0:
            free_vars = {rng.choice(tuple(all_vars))}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        pivot = rng.randrange(m)
        seg_len = max(1, int(round(ratio * m)))
        left = seg_len // 2
        right = seg_len - left - 1

        start = max(0, pivot - left)
        end = min(m, pivot + right + 1)
        while end - start < seg_len and (start > 0 or end < m):
            if start > 0:
                start -= 1
            if end - start >= seg_len:
                break
            if end < m:
                end += 1

        freed_customers = set(route[start:end])

        free_vars = set()
        prev = 0
        for idx, c in enumerate(route):
            if c in freed_customers:
                free_vars.add(f"x_{prev}_{c}")
                if idx + 1 < len(route):
                    nxt = route[idx + 1]
                    if nxt in freed_customers:
                        pass
                prev = c
            else:
                prev = c

        prev = 0
        for c in route:
            if c in freed_customers:
                free_vars.add(f"x_{prev}_{c}")
            prev = c
        if any(c in freed_customers for c in route):
            free_vars.add(f"x_{prev}_0")

        if len(free_vars) < 1:
            free_vars = {rng.choice(tuple(all_vars))}

        target = max(1, int(round(ratio * len(all_vars))))
        if len(free_vars) < target:
            remaining = [v for v in all_vars if v not in free_vars]
            rng.shuffle(remaining)
            for v in remaining:
                free_vars.add(v)
                if len(free_vars) >= target:
                    break

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.15):
    return PivotSegmentDestruction(problem, problem.inst)
