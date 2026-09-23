from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "low_value_item_chain_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "focus_top_k": {"type": "int", "range": [1, 5]},
    },
}


class LowValueItemChainDestruction:
    """Libera todos los setups de uno o más ítems con peor utilidad económica."""

    def __init__(self, problem, inst, focus_top_k: int = 2):
        self.problem = problem
        self.inst = inst
        self.focus_top_k = max(1, int(focus_top_k))

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        groups = self.problem.variable_groups(self.inst)

        item_score = []
        for i in range(n_items):
            setups = sum(1 for t in range(n_periods) if sol[i][t])
            demand = sum(float(self.inst.demand[i][t]) for t in range(n_periods))
            setup_cost = float(self.inst.setup_cost[i])
            holding_cost = float(self.inst.holding_cost[i])
            # Ítems caros de setup y con demanda pequeña son buenos candidatos a reestructurar.
            score = (setup_cost + 1.0) / (demand + 1.0) + 0.25 * holding_cost
            item_score.append((score, -setups, i))

        item_score.sort(reverse=True)
        chosen_items = [i for _, _, i in item_score[: min(self.focus_top_k, n_items)]]

        free_vars = set()
        for i in chosen_items:
            free_vars.update(groups.get(f"t{t}", [])[i:i+1] for t in range(n_periods))
        # flatten the accidental nested structure above safely
        flat_free = set()
        for v in free_vars:
            if isinstance(v, str):
                flat_free.add(v)
            elif isinstance(v, list):
                flat_free.update(v)
        free_vars = flat_free

        target_k = max(1, int(round(ratio * len(assignment))))
        if len(free_vars) < target_k:
            remaining = [v for v in assignment if v not in free_vars]
            rng.shuffle(remaining)
            free_vars.update(remaining[: target_k - len(free_vars)])
        elif len(free_vars) > target_k:
            picked = list(free_vars)
            rng.shuffle(picked)
            free_vars = set(picked[:target_k])

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.20, focus_top_k: int = 2):
    return LowValueItemChainDestruction(problem, problem.inst, focus_top_k=focus_top_k)
