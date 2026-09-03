from random import Random
from typing import Any

from examples.lotsizing.problem_model import LotSizingModel


COMPONENT = {
    "name": "capacity_congestion_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "focus_periods": {"type": "int", "range": [1, 10]},
    },
}


class CapacityCongestionDestruction:
    """Libera setups en los períodos con mayor carga estructural."""

    def __init__(self, problem, inst, focus_periods: int = 2):
        self.problem = problem
        self.inst = inst
        self.focus_periods = focus_periods

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        period_loads = []
        for t in range(n_periods):
            setup_time_load = 0.0
            active_count = 0
            demand_load = 0.0
            for i in range(n_items):
                if sol[i][t]:
                    active_count += 1
                    setup_time_load += self.inst.setup_time[i]
                demand_load += self.inst.demand[i][t]
            score = setup_time_load + 0.01 * demand_load + 0.1 * active_count
            period_loads.append((score, t))

        period_loads.sort(reverse=True)
        focus = [t for _, t in period_loads[: max(1, min(self.focus_periods, n_periods))]]

        candidates = [f"y_{i}_{t}" for t in focus for i in range(n_items)]
        rng.shuffle(candidates)

        free_vars = set(candidates[: min(k, len(candidates))])
        if len(free_vars) < k:
            remaining = [f"y_{i}_{t}" for t in range(n_periods) for i in range(n_items) if f"y_{i}_{t}" not in free_vars]
            rng.shuffle(remaining)
            free_vars.update(remaining[: k - len(free_vars)])

        if not free_vars:
            free_vars.add(next(iter(assignment)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, focus_periods: int = 2):
    return CapacityCongestionDestruction(problem, problem.inst, focus_periods=focus_periods)
