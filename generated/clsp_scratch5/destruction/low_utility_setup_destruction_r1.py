from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "low_utility_setup_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "noise": {"type": "float", "range": [0.0, 1.0]},
    },
}


class LowUtilitySetupDestruction:
    """Libera setups con peor utilidad aparente: lotes caros, cortos o poco prometedores."""

    def __init__(self, problem, inst, noise: float = 0.15):
        self.problem = problem
        self.inst = inst
        self.noise = noise

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        all_vars = [var_name(i, t) for i in range(n_items) for t in range(n_periods)]
        k = max(1, int(round(ratio * len(all_vars))))

        scored = []
        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                # Heurística de utilidad: setups caros/tardíos con poco "soporte" de demanda futura son candidatos débiles.
                future_demand = sum(self.inst.demand[i][tt] for tt in range(t, n_periods))
                support = future_demand + 1.0
                score = (self.inst.setup_cost[i] + 0.5 * self.inst.setup_time[i]) / support
                score += self.noise * rng.random()
                scored.append((score, i, t))

        scored.sort(reverse=True)
        free_vars = {var_name(i, t) for _, i, t in scored[:k]}

        # Si no había suficientes setups activos, completamos con variables aleatorias no liberadas.
        if len(free_vars) < k:
            remaining = [v for v in all_vars if v not in free_vars]
            extra = rng.sample(remaining, min(k - len(free_vars), len(remaining)))
            free_vars.update(extra)

        if not free_vars:
            free_vars.add(rng.choice(all_vars))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2, noise: float = 0.15):
    return LowUtilitySetupDestruction(problem, problem.inst, noise=noise)
