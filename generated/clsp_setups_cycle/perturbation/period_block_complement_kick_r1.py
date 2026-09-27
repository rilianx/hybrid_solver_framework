from __future__ import annotations

from random import Random

COMPONENT = {
    "name": "period_block_complement_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "block_len": {"type": "int", "range": [1, 10]},
    },
}


class PeriodBlockComplementKick:
    def __init__(self, problem, block_len: int = 2):
        self.problem = problem
        self.block_len = max(1, int(block_len))

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.problem.parts.canonical(sol)
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        block = max(1, min(n_periods, int(round(max(1.0, strength))) + self.block_len - 1))
        start = rng.randrange(n_periods)
        periods = [(start + k) % n_periods for k in range(block)]

        s = [list(row) for row in sol]
        # Complement all decisions in selected periods for a random subset of items
        item_order = list(range(n_items))
        rng.shuffle(item_order)
        n_touch = max(1, min(n_items, int(round(strength))))
        touched = set(item_order[:n_touch])

        for i in touched:
            for t in periods:
                s[i][t] = not s[i][t]

        # Guarantee change even in degenerate cases
        out = self.problem.parts.canonical(tuple(tuple(row) for row in s))
        if out == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s[i][t] = not s[i][t]
            out = self.problem.parts.canonical(tuple(tuple(row) for row in s))
        return out


def build_component(problem, **params):
    block_len = params.get("block_len", 2)
    return PeriodBlockComplementKick(problem, block_len=block_len)
