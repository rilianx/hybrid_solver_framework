from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "high_setup_cost_item_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "bias_to_demand": {"type": "bool", "values": [True, False]},
    },
}


class HighSetupCostItemDestruction:
    """Libera todos los setups de los ítems más caros para permitir rediseñar su política temporal."""

    def __init__(self, problem, inst, bias_to_demand: bool = True):
        self.problem = problem
        self.inst = inst
        self.bias_to_demand = bias_to_demand

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods

        def score_item(i: int) -> float:
            base = self.inst.setup_cost[i]
            if self.bias_to_demand:
                demand_scale = sum(self.inst.demand[i]) / max(1.0, sum(sum(row) for row in self.inst.demand))
                return base * (1.0 + demand_scale)
            return base

        items = list(range(n_items))
        items.sort(key=score_item, reverse=True)

        target = max(1, int(round(ratio * n_items * n_periods)))
        free_vars: set[str] = set()

        for i in items:
            for t in range(n_periods):
                free_vars.add(var_name(i, t))
            if len(free_vars) >= target:
                break

        if len(free_vars) > target:
            # Mantener un subconjunto completo por ítem si ya superamos el objetivo.
            chosen_items = []
            for i in items:
                if any(var_name(i, t) in free_vars for t in range(n_periods)):
                    chosen_items.append(i)
                if len(chosen_items) * n_periods >= target:
                    break
            free_vars = {var_name(i, t) for i in chosen_items for t in range(n_periods)}
            if not free_vars:
                free_vars = {var_name(items[0], t) for t in range(n_periods)}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2, bias_to_demand: bool = True):
    return HighSetupCostItemDestruction(problem, problem.inst, bias_to_demand=bias_to_demand)
