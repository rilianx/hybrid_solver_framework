from random import Random

COMPONENT = {
    "name": "isolated_setup_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "lookahead": {"type": "int", "range": [1, 5]},
    },
}


class IsolatedSetupDestruction:
    """Libera setups poco 'útiles': activaciones aisladas o que no parecen sostener mucha demanda futura."""

    def __init__(self, problem, inst, lookahead: int = 2):
        self.problem = problem
        self.inst = inst
        self.lookahead = lookahead

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        target = max(1, int(round(ratio * n_items * n_periods)))

        scored = []
        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                future_demand = sum(self.inst.demand[i][tt] for tt in range(t, min(n_periods, t + self.lookahead + 1)))
                prev_setup = any(sol[i][tt] for tt in range(max(0, t - self.lookahead), t))
                neighbors = sum(
                    1 for j in range(n_items)
                    if j != i and sol[j][t]
                )
                # Menor score = más candidato a liberarse
                score = (future_demand + 1.0) / (1.0 + neighbors + (1.0 if prev_setup else 0.0))
                scored.append((score, i, t))

        scored.sort(key=lambda x: x[0])

        free_vars = set()
        for _, i, t in scored:
            free_vars.add(f"y_{i}_{t}")
            if len(free_vars) >= target:
                break

        if len(free_vars) < target:
            all_vars = [f"y_{i}_{t}" for i in range(n_items) for t in range(n_periods) if f"y_{i}_{t}" not in free_vars]
            rng.shuffle(all_vars)
            for v in all_vars:
                free_vars.add(v)
                if len(free_vars) >= target:
                    break

        if not free_vars:
            free_vars.add(next(iter(assignment.keys())))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, lookahead: int = 2):
    return IsolatedSetupDestruction(problem, problem.inst, lookahead=lookahead)
