from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "two_item_swap_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "swap_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class TwoItemSwapPerturbation:
    def __init__(self, problem: Any, swap_bias: float = 0.5):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.swap_bias = float(swap_bias)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        s = [list(row) for row in sol]

        steps = max(1, int(round(strength)))
        for _ in range(steps):
            if n_items < 2 or n_periods == 0:
                break

            # Prefer periods with at least two active setups, then swap one setup
            # from a "strong" item to a "weak" item in the same period.
            t = rng.randrange(n_periods)
            active_items = [i for i in range(n_items) if s[i][t]]
            inactive_items = [i for i in range(n_items) if not s[i][t]]

            if active_items and inactive_items and rng.random() < self.swap_bias:
                i_on = rng.choice(active_items)
                i_off = rng.choice(inactive_items)
                s[i_on][t] = False
                s[i_off][t] = True
                continue

            # Otherwise, perform a cross-period swap: move one active setup from
            # item i at t to another period of item j, creating a different pattern.
            i = rng.randrange(n_items)
            active_ts = [tt for tt in range(n_periods) if s[i][tt]]
            if not active_ts:
                tt = rng.randrange(n_periods)
                s[i][tt] = True
                continue

            t0 = rng.choice(active_ts)
            j = rng.randrange(n_items)
            if j == i:
                j = (j + 1) % n_items

            target_ts = [tt for tt in range(n_periods) if not s[j][tt]]
            if not target_ts:
                s[i][t0] = not s[i][t0]
                continue

            t1 = rng.choice(target_ts)
            s[i][t0] = False
            s[j][t1] = True

        out = tuple(tuple(row) for row in s)
        if out == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s = [list(row) for row in sol]
            s[i][t] = not s[i][t]
            out = tuple(tuple(row) for row in s)
        return out


def build_component(problem, **params):
    swap_bias = params.get("swap_bias", 0.5)
    return TwoItemSwapPerturbation(problem, swap_bias=swap_bias)
