from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "uniform_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class UniformArcDestruction:
    """Libera arcos estructurales al azar de forma uniforme."""

    def __init__(self, problem, **params):
        self.problem = problem

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = dict(self.problem.to_assignment(sol))
        vars_list = list(assignment.keys())
        n_vars = len(vars_list)
        k = max(1, int(round(ratio * n_vars)))
        k = min(k, n_vars)

        chosen = set(rng.sample(vars_list, k))
        partial = {v: val for v, val in assignment.items() if v not in chosen}
        return partial, chosen


def build_component(problem, **params):
    ratio = params.get("ratio", 0.2)
    return UniformArcDestruction(problem, ratio=ratio)
