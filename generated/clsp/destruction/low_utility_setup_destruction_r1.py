from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "low_utility_setup_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "future_weight": {"type": "float", "range": [0.0, 2.0]},
        "randomness": {"type": "float", "range": [0.0, 1.0]},
    },
}


class LowUtilitySetupDestruction:
    """Libera setups con baja utilidad estimada: poco ahorro de setups frente a inventario."""

    def __init__(self, problem, inst, future_weight: float = 1.0, randomness: float = 0.2):
        self.problem = problem
        self.inst = inst
        self.future_weight = future_weight
        self.randomness = randomness

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        scored = []
        for i in range(n_items):
            future_demand_prefix = [0.0] * n_periods
            acc = 0.0
            for t in range(n_periods - 1, -1, -1):
                acc += self.inst.demand[i][t]
                future_demand_prefix[t] = acc
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                demand_next = future_demand_prefix[t + 1] if t + 1 < n_periods else 0.0
                saving = self.inst.setup_cost[i] - self.future_weight * self.inst.holding_cost[i] * demand_next
                score = saving + self.randomness * rng.random()
                scored.append((score, i, t))

        scored.sort(key=lambda x: x[0])
        chosen: set[str] = set()

        for _, i, t in scored:
            chosen.add(var_name(i, t))
            if len(chosen) >= k:
                break

        while len(chosen) < k:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            chosen.add(var_name(i, t))

        if not chosen:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            chosen.add(var_name(i, t))

        free_vars = chosen
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, future_weight: float = 1.0, randomness: float = 0.2):
    return LowUtilitySetupDestruction(problem, problem.inst, future_weight=future_weight, randomness=randomness)
