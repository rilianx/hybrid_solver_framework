from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "congested_period_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
        "focus_strength": {"type": "float", "range": [0.0, 1.0]},
    },
}


class CongestedPeriodDestruction:
    """Libera setups en los períodos más cargados, priorizando los que rozan o exceden capacidad."""

    def __init__(self, problem, inst, focus_strength: float = 0.65):
        self.problem = problem
        self.inst = inst
        self.focus_strength = focus_strength

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        period_loads = []
        for t in range(n_periods):
            prod = sum(self.inst.demand[i][t] for i in range(n_items) if sol[i][t])
            st = sum(self.inst.setup_time[i] for i in range(n_items) if sol[i][t])
            slack = self.inst.capacity[t] - (prod + st)
            period_loads.append((t, slack, prod + st))

        period_loads.sort(key=lambda x: (x[1], -x[2]))  # menos holgura primero
        candidate_periods = [t for t, _, _ in period_loads]

        free_vars: set[str] = set()
        target_periods = max(1, int(round((0.25 + 0.5 * self.focus_strength) * n_periods)))
        chosen_periods = candidate_periods[:target_periods]

        def add_period(t: int) -> None:
            for i in range(n_items):
                if len(free_vars) >= k:
                    return
                free_vars.add(var_name(i, t))

        for t in chosen_periods:
            add_period(t)
            if len(free_vars) >= k:
                break

        while len(free_vars) < k:
            t = rng.choice(candidate_periods)
            i = rng.randrange(n_items)
            free_vars.add(var_name(i, t))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, focus_strength: float = 0.65):
    return CongestedPeriodDestruction(problem, problem.inst, focus_strength=focus_strength)
