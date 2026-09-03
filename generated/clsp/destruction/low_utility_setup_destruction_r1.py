from random import Random
from typing import Any

from examples.lotsizing.problem_model import LotSizingModel


COMPONENT = {
    "name": "low_utility_setup_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "noise": {"type": "float", "range": [0.0, 0.5]},
    },
}


class LowUtilitySetupDestruction:
    """Libera setups que parecen menos útiles: poco costo ahorrado vs. carga inducida."""

    def __init__(self, problem, inst, noise: float = 0.1):
        self.problem = problem
        self.inst = inst
        self.noise = noise

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        scored = []
        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                future_demand = sum(self.inst.demand[i][u] for u in range(t, n_periods))
                setup_gain = self.inst.setup_cost[i]
                burden = self.inst.setup_time[i] + 0.1 * future_demand
                score = setup_gain / (1.0 + burden)
                if self.noise > 0:
                    score *= 1.0 + rng.uniform(-self.noise, self.noise)
                scored.append((score, f"y_{i}_{t}"))

        if not scored:
            all_vars = [f"y_{i}_{t}" for i in range(n_items) for t in range(n_periods)]
            rng.shuffle(all_vars)
            free_vars = set(all_vars[:1])
        else:
            scored.sort()
            free_vars = {var for _, var in scored[: min(k, len(scored))]}
            if len(free_vars) < k:
                remaining = [f"y_{i}_{t}" for i in range(n_items) for t in range(n_periods) if f"y_{i}_{t}" not in free_vars]
                rng.shuffle(remaining)
                free_vars.update(remaining[: k - len(free_vars)])

        if not free_vars:
            free_vars.add(next(iter(assignment)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, noise: float = 0.1):
    return LowUtilitySetupDestruction(problem, problem.inst, noise=noise)
