from __future__ import annotations

from random import Random
from typing import Any


COMPONENT = {
    "name": "capacity_window_rewire",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "window_frac": {"type": "float", "range": [0.1, 0.6]},
    },
}


class CapacityWindowRewire:
    def __init__(self, problem, window_frac: float = 0.3):
        self.problem = problem
        self.window_frac = window_frac

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.problem.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        w = max(1, min(n_periods, int(round(self.window_frac * n_periods))))
        start = rng.randrange(0, n_periods - w + 1)
        end = start + w

        s = [list(row) for row in sol]
        affected = [(i, t) for i in range(n_items) for t in range(start, end)]
        rng.shuffle(affected)

        n_changes = max(1, min(len(affected), int(round(strength * max(1, w)))))
        for i, t in affected[:n_changes]:
            s[i][t] = not s[i][t]

        # Guarantee change.
        if tuple(tuple(row) for row in s) == sol:
            i, t = affected[0]
            s[i][t] = not s[i][t]

        return tuple(tuple(row) for row in s)


def build_component(problem, **params):
    return CapacityWindowRewire(problem, window_frac=float(params.get("window_frac", 0.3)))
