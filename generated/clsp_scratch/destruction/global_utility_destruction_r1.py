from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "global_utility_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "randomness": {"type": "float", "range": [0.0, 0.6]},
    },
}


class GlobalUtilityDestruction:
    """Libera los setups globalmente menos 'útiles' para reoptimizar la estructura."""

    def __init__(self, problem, inst, randomness: float = 0.15):
        self.problem = problem
        self.inst = inst
        self.randomness = max(0.0, float(randomness))

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods

        candidates = []
        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                # Utilidad estimada: cuánto "aprovecha" el setup en su propio período.
                demand_here = float(self.inst.demand[i][t])
                future_demand = sum(float(self.inst.demand[i][tt]) for tt in range(t, n_periods))
                holding_penalty_proxy = 0.0
                for tt in range(t + 1, n_periods):
                    holding_penalty_proxy += float(self.inst.holding_cost[i]) * float(self.inst.demand[i][tt]) * (tt - t)
                utility = (
                    float(self.inst.setup_cost[i]) * 0.0
                    + demand_here
                    + 0.5 * future_demand
                    - 0.01 * holding_penalty_proxy
                    - float(self.inst.setup_time[i])
                )
                noise = (rng.random() - 0.5) * self.randomness * max(1.0, abs(utility))
                candidates.append((utility + noise, i, t))

        if not candidates:
            free_vars = {next(iter(assignment))}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        candidates.sort(key=lambda x: (x[0], x[1], x[2]))
        k = max(1, int(round(ratio * len(assignment))))
        free_vars = {f"y_{i}_{t}" for _, i, t in candidates[:k]}

        if len(free_vars) < k:
            remaining = [v for v in assignment if v not in free_vars]
            rng.shuffle(remaining)
            free_vars.update(remaining[: k - len(free_vars)])

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.20, randomness: float = 0.15):
    return GlobalUtilityDestruction(problem, problem.inst, randomness=randomness)
