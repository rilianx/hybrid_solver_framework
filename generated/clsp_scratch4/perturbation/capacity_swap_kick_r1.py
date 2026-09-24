from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel


COMPONENT = {
    "name": "capacity_swap_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 6.0]}},
}


class CapacitySwapKick:
    def __init__(self, problem: LotSizingModel):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    @staticmethod
    def _tupled(y):
        return tuple(tuple(row) for row in y)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        y = [list(row) for row in sol]

        # Identify congested periods by current setup-time usage.
        load = []
        for t in range(n_periods):
            load_t = sum(inst.setup_time[i] for i in range(n_items) if y[i][t])
            load.append(load_t)

        worst_periods = sorted(range(n_periods), key=lambda t: load[t], reverse=True)
        n_ops = max(1, int(round(strength)))

        changed = False
        for _ in range(n_ops):
            if not worst_periods:
                break
            t = worst_periods[0]
            # Prefer an item with a setup in the congested period and room in another period.
            items_here = [i for i in range(n_items) if y[i][t]]
            if not items_here:
                continue
            i = rng.choice(items_here)

            # Try swapping to a less loaded period to relieve congestion.
            target_periods = sorted(range(n_periods), key=lambda tt: load[tt])
            target = None
            for tt in target_periods:
                if tt != t and not y[i][tt]:
                    target = tt
                    break
            if target is None:
                continue

            # Keep at least one setup for the item.
            if sum(y[i]) <= 1:
                continue

            y[i][t] = False
            y[i][target] = True
            load[t] -= inst.setup_time[i]
            load[target] += inst.setup_time[i]
            changed = True
            worst_periods = sorted(range(n_periods), key=lambda tt: load[tt], reverse=True)

        if not changed:
            # Fallback: force a two-bit swap on a random item.
            i = rng.randrange(n_items)
            t1 = rng.randrange(n_periods)
            t2 = (t1 + 1 + rng.randrange(max(1, n_periods - 1))) % n_periods
            y[i][t1] = not y[i][t1]
            y[i][t2] = True
            if not any(y[i]):
                y[i][t2] = True

        out = self._tupled(y)
        if out == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            y2 = [list(row) for row in out]
            y2[i][t] = not y2[i][t]
            if not any(y2[i]):
                y2[i][(t + 1) % n_periods] = True
            out = self._tupled(y2)
        return out


def build_component(problem, **params):
    strength = params.get("strength", 2.0)
    return CapacitySwapKick(problem)
