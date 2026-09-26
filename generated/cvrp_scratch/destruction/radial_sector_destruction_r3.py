from __future__ import annotations

from math import ceil
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
        if not assignment:
            return assignment, set()

        if not groups:
            v = next(iter(assignment))
            return {k: val for k, val in assignment.items() if k != v}, {v}

        group_names = sorted(groups.keys())

        # Select a contiguous sector block; larger ratio => never fewer selected groups.
        n_groups = len(group_names)
        target_groups = min(n_groups, max(1, int(ratio * n_groups) + 1))
        start = rng.randrange(n_groups)
        selected_groups = [
            group_names[(start + offset) % n_groups] for offset in range(target_groups)
        ]

        candidate_vars: list[str] = []
        for g in selected_groups:
            candidate_vars.extend(v for v in groups.get(g, ()) if v in assignment)

        if not candidate_vars:
            v = next(iter(assignment))
            return {k: val for k, val in assignment.items() if k != v}, {v}

        candidate_vars.sort()
        target_vars = min(len(candidate_vars), max(1, ceil(ratio * len(assignment))))
        free_vars = set(candidate_vars[:target_vars])

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = params.get("ratio", 0.25)
    return RadialSectorDestruction(problem, problem.inst, ratio=ratio)
