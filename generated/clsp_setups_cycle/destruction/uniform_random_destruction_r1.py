from random import Random
from typing import Any

COMPONENT = {
    "name": "uniform_random_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
    },
}


class UniformRandomDestruction:
    """Libera variables estructurales al azar, preservando siempre al menos una."""

    def __init__(self, problem, ratio: float):
        self.problem = problem
        self.ratio = float(ratio)

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        vars_ = list(assignment.keys())
        n = len(vars_)
        if n == 0:
            return {}, set()

        k = max(1, min(n, int(round(max(0.0, ratio) * n))))
        chosen = set(rng.sample(vars_, k)) if k < n else set(vars_)

        partial = {v: assignment[v] for v in vars_ if v not in chosen}
        return partial, chosen


def build_component(problem, ratio: float = 0.25):
    return UniformRandomDestruction(problem, ratio)
