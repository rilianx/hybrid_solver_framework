from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "period_compaction_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 12.0]},
        "window": {"type": "int", "range": [2, 6]},
    },
}


class PeriodCompactionPerturbation:
    def __init__(self, problem: Any, window: int = 3):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.window = max(2, int(window))

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        s = [list(row) for row in sol]

        rounds = max(1, int(round(strength)))
        for _ in range(rounds):
            if n_periods == 1:
                i = rng.randrange(n_items)
                s[i][0] = not s[i][0]
                continue

            w = min(self.window, n_periods)
            start = rng.randrange(0, n_periods - w + 1)
            end = start + w

            # Compaction: inside the window, try to keep at most one setup per item
            # by moving an active setup to the left boundary if possible.
            candidates = [i for i in range(n_items) if any(s[i][t] for t in range(start, end))]
            if not candidates:
                i = rng.randrange(n_items)
                t = rng.randrange(n_periods)
                s[i][t] = not s[i][t]
                continue

            i = rng.choice(candidates)
            active = [t for t in range(start, end) if s[i][t]]
            if not active:
                t = rng.randrange(n_periods)
                s[i][t] = not s[i][t]
                continue

            # Remove one setup in the window and add one at a boundary outside the window
            t_remove = rng.choice(active)
            t_add_choices = list(range(0, start)) + list(range(end, n_periods))
            if not t_add_choices:
                # fallback: move within window to another position
                t_add_choices = [t for t in range(start, end) if t != t_remove]
            if not t_add_choices:
                s[i][t_remove] = not s[i][t_remove]
                continue

            t_add = rng.choice(t_add_choices)
            s[i][t_remove] = False
            s[i][t_add] = True

        out = tuple(tuple(row) for row in s)
        if out == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s = [list(row) for row in sol]
            s[i][t] = not s[i][t]
            out = tuple(tuple(row) for row in s)
        return out


def build_component(problem, **params):
    window = params.get("window", 3)
    return PeriodCompactionPerturbation(problem, window=window)
