from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "item_chain_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "window": {"type": "int", "range": [1, 8]},
        "extend_left": {"type": "bool", "range": [0, 1]},
    },
}


class ItemChainDestruction:
    """Libera un ítem entero y una cadena temporal alrededor de uno de sus setups."""

    def __init__(self, problem, inst, window: int = 2, extend_left: bool = True):
        self.problem = problem
        self.inst = inst
        self.window = window
        self.extend_left = extend_left

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        item_scores = []
        for i in range(n_items):
            setups = [t for t in range(n_periods) if sol[i][t]]
            if setups:
                span = setups[-1] - setups[0] + 1
                score = len(setups) * 2.0 + span + self.inst.setup_cost[i] / max(1.0, self.inst.holding_cost[i])
            else:
                score = 0.0
            item_scores.append((score, i))
        item_scores.sort(reverse=True)

        chosen: set[str] = set()
        if item_scores:
            _, i0 = item_scores[0]
            for t in range(n_periods):
                chosen.add(var_name(i0, t))

            active = [t for t in range(n_periods) if sol[i0][t]]
            if active:
                pivot = rng.choice(active)
            else:
                pivot = rng.randrange(n_periods)

            left = max(0, pivot - self.window if self.extend_left else pivot)
            right = min(n_periods - 1, pivot + self.window)
            for t in range(left, right + 1):
                chosen.add(var_name(i0, t))

        while len(chosen) < k:
            i = rng.randrange(n_items)
            if rng.random() < 0.7:
                t_candidates = [t for t in range(n_periods) if sol[i][t]]
                t = rng.choice(t_candidates) if t_candidates else rng.randrange(n_periods)
            else:
                t = rng.randrange(n_periods)
            chosen.add(var_name(i, t))

        free_vars = chosen
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, window: int = 2, extend_left: bool = True):
    return ItemChainDestruction(problem, problem.inst, window=window, extend_left=extend_left)
