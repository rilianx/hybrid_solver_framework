from __future__ import annotations

from random import Random


COMPONENT = {
    "name": "critical_item_shift",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "aggressiveness": {"type": "float", "range": [0.2, 2.0]},
    },
}


class CriticalItemShift:
    def __init__(self, problem, aggressiveness: float = 1.0):
        self.problem = problem
        self.aggressiveness = aggressiveness

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.problem.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        # Score items by setup cost weighted by setup frequency in the current solution.
        scores = []
        for i in range(n_items):
            freq = sum(1 for t in range(n_periods) if sol[i][t])
            scores.append((inst.setup_cost[i] * (1.0 + 0.5 * freq), i))
        scores.sort(reverse=True)

        k = max(1, min(n_items, int(round(self.aggressiveness * strength))))
        chosen_items = [i for _, i in scores[:k]]
        chosen_item = rng.choice(chosen_items)

        s = [list(row) for row in sol]
        t = rng.randrange(n_periods)

        # Try to move a setup within a local neighborhood to create a different temporal pattern.
        offsets = [d for d in range(-n_periods, n_periods + 1) if d != 0]
        rng.shuffle(offsets)
        moved = False
        for d in offsets:
            tt = t + d
            if 0 <= tt < n_periods:
                s[chosen_item][t] = False
                s[chosen_item][tt] = True
                moved = True
                break

        if not moved:
            s[chosen_item][t] = not s[chosen_item][t]

        new_sol = tuple(tuple(row) for row in s)
        if new_sol == sol:
            s[chosen_item][t] = not s[chosen_item][t]
            new_sol = tuple(tuple(row) for row in s)
        return new_sol


def build_component(problem, **params):
    return CriticalItemShift(problem, aggressiveness=float(params.get("aggressiveness", 1.0)))
