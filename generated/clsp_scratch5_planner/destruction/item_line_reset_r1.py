from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "item_line_reset",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
    },
}


class ItemLineResetDestruction:
    """Libera todos los setups de una o varias líneas de producto a lo largo del horizonte."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        target = max(1, int(round(ratio * n_items)))
        target = min(target, n_items)

        # Preferir líneas con más setups actuales: suelen tener más estructura
        # que conviene reconstruir desde cero.
        item_scores = []
        for i in range(n_items):
            setups = sum(1 for t in range(n_periods) if sol[i][t])
            item_scores.append((setups, self.inst.setup_cost[i], i))

        item_scores.sort(key=lambda x: (-x[0], -x[1], x[2]))

        chosen: set[int] = set()
        for _, _, i in item_scores:
            if len(chosen) >= target:
                break
            chosen.add(i)

        # Pequeña inyección de azar para diversificar entre ítems con estructura similar.
        candidates = [i for i in range(n_items) if i not in chosen]
        rng.shuffle(candidates)
        while len(chosen) < target and candidates:
            chosen.add(candidates.pop())

        free_vars = {var_name(i, t) for i in chosen for t in range(n_periods)}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = float(params.get("ratio", 0.25))
    return ItemLineResetDestruction(problem, problem.inst)
