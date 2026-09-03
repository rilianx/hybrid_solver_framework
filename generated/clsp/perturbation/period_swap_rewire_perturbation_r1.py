from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import LotSizingModel, CLSPInstance


COMPONENT = {
    "name": "period_swap_rewire_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "pairs": {"type": "int", "range": [1, 6]},
        "target_scope": {"type": "cat", "values": ["all_items", "active_items_only"]},
    },
}


class PeriodSwapRewirePerturbation:
    def __init__(self, problem: LotSizingModel, pairs: int = 1, target_scope: str = "all_items"):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.pairs = pairs
        self.target_scope = target_scope

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods < 2:
            return sol

        k = max(1, min(self.pairs, int(round(strength))))
        new = [list(row) for row in sol]

        for _ in range(k):
            t1, t2 = rng.sample(range(n_periods), 2)
            items = list(range(n_items))
            if self.target_scope == "active_items_only":
                items = [i for i in items if sol[i][t1] or sol[i][t2]]
                if not items:
                    items = list(range(n_items))
            # swap a random non-empty subset between the two periods
            subset_size = rng.randint(1, len(items))
            chosen = set(rng.sample(items, subset_size))
            for i in chosen:
                new[i][t1], new[i][t2] = new[i][t2], new[i][t1]

        candidate = tuple(tuple(r) for r in new)
        if candidate == sol:
            # Force a distinct change by flipping one bit in a random period.
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            new = [list(row) for row in sol]
            new[i][t] = not new[i][t]
            candidate = tuple(tuple(r) for r in new)
        return candidate


def build_component(problem, **params):
    return PeriodSwapRewirePerturbation(
        problem,
        pairs=int(params.get("pairs", 1)),
        target_scope=str(params.get("target_scope", "all_items")),
    )
