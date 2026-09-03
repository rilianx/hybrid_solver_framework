from random import Random

COMPONENT = {
    "name": "capacity_bottleneck_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "window": {"type": "int", "range": [1, 4]},
    },
}


class CapacityBottleneckDestruction:
    """Libera setups en los períodos más cargados, ampliando la vecindad alrededor del cuello de botella."""

    def __init__(self, problem, inst, window: int = 2):
        self.problem = problem
        self.inst = inst
        self.window = window

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        target = max(1, int(round(ratio * n_items * n_periods)))

        loads = []
        for t in range(n_periods):
            used = sum(self.inst.setup_time[i] for i in range(n_items) if sol[i][t])
            loads.append((used / self.inst.capacity[t] if self.inst.capacity[t] > 0 else float("inf"), t))
        loads.sort(reverse=True)

        free_vars = set()
        for _, t0 in loads:
            if len(free_vars) >= target:
                break
            for dt in range(-self.window, self.window + 1):
                t = t0 + dt
                if 0 <= t < n_periods:
                    for i in range(n_items):
                        if sol[i][t]:
                            free_vars.add(f"y_{i}_{t}")
                            if len(free_vars) >= target:
                                break
                    if len(free_vars) >= target:
                        break
            if len(free_vars) >= target:
                break

        if len(free_vars) < target:
            candidates = [f"y_{i}_{t}" for t in range(n_periods) for i in range(n_items) if f"y_{i}_{t}" not in free_vars]
            rng.shuffle(candidates)
            for v in candidates:
                free_vars.add(v)
                if len(free_vars) >= target:
                    break

        if not free_vars:
            free_vars.add(next(iter(assignment.keys())))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, window: int = 2):
    return CapacityBottleneckDestruction(problem, problem.inst, window=window)
