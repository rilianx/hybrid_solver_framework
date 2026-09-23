from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "most_congested_period_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "window_radius": {"type": "int", "range": [0, 3]},
    },
}


class MostCongestedPeriodDestruction:
    """Libera setups en los períodos más cargados, para que el LNS reubique producción."""

    def __init__(self, problem, inst, window_radius: int = 1):
        self.problem = problem
        self.inst = inst
        self.window_radius = window_radius

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods

        period_loads = []
        for t in range(n_periods):
            load = sum(
                self.inst.setup_time[i] + self.inst.demand[i][t]
                for i in range(n_items)
                if sol[i][t]
            )
            period_loads.append((load / max(self.inst.capacity[t], 1e-9), t))

        target = max(1, int(round(ratio * n_items * n_periods)))
        free_vars: set[str] = set()

        for _, t in sorted(period_loads, reverse=True):
            for tt in range(max(0, t - self.window_radius), min(n_periods, t + self.window_radius + 1)):
                for i in range(n_items):
                    free_vars.add(var_name(i, tt))
            if len(free_vars) >= target:
                break

        if not free_vars:
            t = max(range(n_periods), key=lambda j: period_loads[j][0])
            free_vars = {var_name(i, t) for i in range(n_items)}

        if len(free_vars) > target:
            chosen = list(free_vars)
            rng.shuffle(chosen)
            free_vars = set(chosen[: max(1, target)])

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.18, window_radius: int = 1):
    return MostCongestedPeriodDestruction(problem, problem.inst, window_radius=window_radius)
