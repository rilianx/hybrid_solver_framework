from random import Random
from typing import Any

COMPONENT = {
    "name": "setup_intensity_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
        "focus_setup_cost": {"type": "bool", "values": [True, False]},
    },
}


class SetupIntensityDestruction:
    """Libera los ítems más “caros” en setups, borrando filas completas de la matriz y luego ajustando."""

    def __init__(self, problem, ratio: float, focus_setup_cost: bool):
        self.problem = problem
        self.ratio = float(ratio)
        self.focus_setup_cost = bool(focus_setup_cost)

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        inst = self.problem.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        vars_ = list(assignment.keys())
        if not vars_:
            return {}, set()

        target = max(1, min(len(vars_), int(round(max(0.0, ratio) * len(vars_)))))

        if self.focus_setup_cost:
            order = sorted(range(n_items), key=lambda i: (inst.setup_cost[i], inst.setup_time[i]), reverse=True)
        else:
            order = sorted(range(n_items), key=lambda i: (inst.setup_time[i], inst.setup_cost[i]), reverse=True)

        free_vars: set[str] = set()
        for i in order:
            row_vars = {f"y_{i}_{t}" for t in range(n_periods) if f"y_{i}_{t}" in assignment}
            if len(free_vars) + len(row_vars) <= target:
                free_vars |= row_vars
            else:
                break

        if len(free_vars) < target:
            remaining = [v for v in vars_ if v not in free_vars]
            need = min(len(remaining), target - len(free_vars))
            if need > 0:
                # Mezcla aleatoria para completar, evitando sesgo excesivo.
                free_vars |= set(rng.sample(remaining, need))

        if len(free_vars) >= len(vars_):
            keep = rng.choice(vars_)
            free_vars.remove(keep)

        partial = {v: assignment[v] for v in vars_ if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, focus_setup_cost: bool = True):
    return SetupIntensityDestruction(problem, ratio, focus_setup_cost)
