from __future__ import annotations

from random import Random

COMPONENT = {
    "name": "column_shuffle_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "window": {"type": "int", "range": [1, 10]},
    },
}


class ColumnShuffleKick:
    def __init__(self, problem, window: int = 3):
        self.problem = problem
        self.window = max(1, int(window))

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.problem.parts.canonical(sol)
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        t0 = rng.randrange(n_periods)
        width = max(1, min(n_periods, int(round(max(1.0, strength))) + self.window - 1))
        periods = [(t0 + k) % n_periods for k in range(width)]

        s = [list(row) for row in sol]
        for t in periods:
            col = [s[i][t] for i in range(n_items)]
            rng.shuffle(col)
            # Avoid no-op when all values identical
            if all(col[i] == s[i][t] for i in range(n_items)):
                i = rng.randrange(n_items)
                col[i] = not col[i]
            for i in range(n_items):
                s[i][t] = bool(col[i])

        out = self.problem.parts.canonical(tuple(tuple(row) for row in s))
        if out == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s[i][t] = not s[i][t]
            out = self.problem.parts.canonical(tuple(tuple(row) for row in s))
        return out


def build_component(problem, **params):
    window = params.get("window", 3)
    return ColumnShuffleKick(problem, window=window)
