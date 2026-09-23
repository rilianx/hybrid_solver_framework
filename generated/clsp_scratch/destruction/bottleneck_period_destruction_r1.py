from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "bottleneck_period_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "neighbor_span": {"type": "int", "range": [0, 2]},
    },
}


class BottleneckPeriodDestruction:
    """Libera setups en los períodos más cargados/cercanos a saturación."""

    def __init__(self, problem, inst, neighbor_span: int = 1):
        self.problem = problem
        self.inst = inst
        self.neighbor_span = max(0, int(neighbor_span))

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        groups = self.problem.variable_groups(self.inst)

        period_load = []
        for t in range(n_periods):
            load = 0.0
            for i in range(n_items):
                if sol[i][t]:
                    load += float(self.inst.setup_time[i]) + float(self.inst.demand[i][t])
            slack = float(self.inst.capacity[t]) - load
            period_load.append((slack, load, t))

        period_load.sort(key=lambda x: (x[0], -x[1], x[2]))  # menor holgura primero
        target_vars = []
        target_periods = set()

        k_periods = max(1, int(round(ratio * n_periods)))
        for _, _, t in period_load[:k_periods]:
            for tt in range(max(0, t - self.neighbor_span), min(n_periods, t + self.neighbor_span + 1)):
                target_periods.add(tt)

        for t in sorted(target_periods):
            target_vars.extend(groups.get(f"t{t}", []))

        if not target_vars:
            target_vars = [v for v in assignment.keys()]

        k = max(1, int(round(ratio * len(assignment))))
        if len(target_vars) < k:
            remaining = [v for v in assignment if v not in target_vars]
            rng.shuffle(remaining)
            target_vars.extend(remaining[: max(0, k - len(target_vars))])
        else:
            rng.shuffle(target_vars)
            target_vars = target_vars[:k]

        free_vars = set(target_vars)
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.20, neighbor_span: int = 1):
    return BottleneckPeriodDestruction(problem, problem.inst, neighbor_span=neighbor_span)
