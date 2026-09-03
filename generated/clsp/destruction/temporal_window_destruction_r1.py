from random import Random
from typing import Any

from examples.lotsizing.problem_model import LotSizingModel


COMPONENT = {
    "name": "temporal_window_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "window_size": {"type": "int", "range": [1, 20]},
    },
}


class TemporalWindowDestruction:
    """Libera setups dentro de una ventana de períodos contiguos."""

    def __init__(self, problem, inst, window_size: int = 3):
        self.problem = problem
        self.inst = inst
        self.window_size = window_size

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        if n_periods <= self.window_size:
            start = 0
            end = n_periods
        else:
            start = rng.randrange(0, n_periods - self.window_size + 1)
            end = start + self.window_size

        window_vars = [f"y_{i}_{t}" for t in range(start, end) for i in range(n_items)]
        rng.shuffle(window_vars)

        free_vars = set(window_vars[: min(k, len(window_vars))])
        if len(free_vars) < k:
            remaining = [f"y_{i}_{t}" for t in range(n_periods) for i in range(n_items) if f"y_{i}_{t}" not in free_vars]
            rng.shuffle(remaining)
            free_vars.update(remaining[: k - len(free_vars)])

        if not free_vars:
            free_vars.add(next(iter(assignment)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, window_size: int = 3):
    return TemporalWindowDestruction(problem, problem.inst, window_size=window_size)
