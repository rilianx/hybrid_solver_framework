from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel


COMPONENT = {
    "name": "period_block_destroy_repair",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 6.0]}},
}


class PeriodBlockDestroyRepair:
    def __init__(self, problem: LotSizingModel):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    @staticmethod
    def _as_tuple(y):
        return tuple(tuple(row) for row in y)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        y = [list(row) for row in sol]

        block_len = max(1, min(n_periods, int(round(strength))))
        if block_len == 1 and n_periods > 1:
            block_len = 2

        start = rng.randrange(0, n_periods - block_len + 1)
        block = range(start, start + block_len)

        # Destroy: remove setups in a time block, keeping at least one setup per item.
        removed_any = False
        for t in block:
            for i in range(n_items):
                if y[i][t] and sum(y[i]) > 1:
                    y[i][t] = False
                    removed_any = True

        # Repair: for each item that lost all setups or is now too sparse,
        # place a setup in the cheapest/least-loaded period outside the block.
        if not removed_any:
            i = rng.randrange(n_items)
            t = rng.choice(list(block))
            y[i][t] = not y[i][t]
            if not any(y[i]):
                y[i][(t + 1) % n_periods] = True
            return self._as_tuple(y)

        # Add at most one setup per affected item using a simple score.
        period_load = [0.0] * n_periods
        for t in range(n_periods):
            period_load[t] = sum(inst.setup_time[i] for i in range(n_items) if y[i][t])

        affected = set()
        for i in range(n_items):
            if not any(y[i]):
                affected.add(i)

        # Also consider items whose setups are all inside the destroyed block.
        for i in range(n_items):
            on = [t for t in range(n_periods) if y[i][t]]
            if on and all(t in block for t in on):
                affected.add(i)

        for i in affected:
            candidates = [t for t in range(n_periods) if t not in block]
            if not candidates:
                candidates = list(range(n_periods))
            def score(t):
                future_demand = sum(inst.demand[i][tt] for tt in range(t, n_periods))
                return (period_load[t], -future_demand, t)
            t_best = min(candidates, key=score)
            y[i][t_best] = True
            period_load[t_best] += inst.setup_time[i]

        out = self._as_tuple(y)
        if out == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            y2 = [list(row) for row in out]
            y2[i][t] = not y2[i][t]
            if not any(y2[i]):
                y2[i][(t + 1) % n_periods] = True
            out = self._as_tuple(y2)
        return out


def build_component(problem, **params):
    strength = params.get("strength", 2.0)
    return PeriodBlockDestroyRepair(problem)
