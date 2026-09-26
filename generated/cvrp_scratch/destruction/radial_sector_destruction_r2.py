from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "radial_sector_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RadialSectorDestruction:
    """Libera un sector angular contiguo de arcos de salida, no clientes aislados."""

    def __init__(self, problem, inst, ratio: float = 0.25):
        self.problem = problem
        self.inst = inst
        self.ratio = ratio

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)

        groups = self.problem.variable_groups(self.inst)
        if not groups:
            if assignment:
                v = next(iter(assignment))
                return {k: val for k, val in assignment.items() if k != v}, {v}
            return assignment, set()

        group_names = sorted(groups.keys())
        target = max(1, int(round(ratio * len(group_names))))
        start = rng.randrange(len(group_names))
        selected_groups = {
            group_names[(start + offset) % len(group_names)] for offset in range(target)
        }

        free_vars: set[str] = set()
        for g in selected_groups:
            for v in groups.get(g, ()):
                if v in assignment:
                    free_vars.add(v)

        if not free_vars and assignment:
            free_vars.add(next(iter(assignment)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = params.get("ratio", 0.25)
    return RadialSectorDestruction(problem, problem.inst, ratio=ratio)
