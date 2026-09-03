from random import Random
from typing import Any

COMPONENT = {
    "name": "capacity_bottleneck_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class CapacityBottleneckDestruction:
    """Libera setups en los períodos más cargados por capacidad."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst
        self._groups = problem.variable_groups(self.inst)

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        k = max(1, int(round(ratio * n_items * n_periods)))

        loads = []
        for t in range(n_periods):
            used = sum(self.inst.setup_time[i] for i in range(n_items) if sol[i][t])
            load = used / max(self.inst.capacity[t], 1e-9)
            loads.append((load, t))
        loads.sort(reverse=True)

        free_vars: set[str] = set()
        period_order = [t for _, t in loads]
        for t in period_order:
            period_vars = list(self._groups[f"t{t}"])
            rng.shuffle(period_vars)
            for v in period_vars:
                if v not in free_vars:
                    free_vars.add(v)
                    if len(free_vars) >= k:
                        break
            if len(free_vars) >= k:
                break

        if not free_vars:
            t = rng.randrange(n_periods)
            free_vars.add(rng.choice(self._groups[f"t{t}"]))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25):
    return CapacityBottleneckDestruction(problem)
