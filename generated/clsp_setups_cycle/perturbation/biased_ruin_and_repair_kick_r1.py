from __future__ import annotations

from random import Random

COMPONENT = {
    "name": "biased_ruin_and_repair_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "ruin_fraction": {"type": "float", "range": [0.05, 0.8]},
    },
}


class BiasedRuinAndRepairKick:
    def __init__(self, problem, ruin_fraction: float = 0.2):
        self.problem = problem
        self.ruin_fraction = float(ruin_fraction)

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.problem.parts.canonical(sol)
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        s = [list(row) for row in sol]
        total = n_items * n_periods
        k = max(1, min(total, int(round(max(1.0, strength) * self.ruin_fraction * total / 4.0))))
        # Ruin a scattered set of positions, biased toward later periods
        candidates = [(i, t) for i in range(n_items) for t in range(n_periods)]
        candidates.sort(key=lambda it: (it[1], rng.random()))
        chosen = set()
        step = max(1, total // max(1, k))
        idx = rng.randrange(min(step, len(candidates)))
        while len(chosen) < k and candidates:
            i, t = candidates[idx % len(candidates)]
            chosen.add((i, t))
            idx += step

        if not chosen:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            chosen.add((i, t))

        for i, t in chosen:
            s[i][t] = not s[i][t]

        # Repair phase: add a short coherent burst in one random item to avoid triviality
        i0 = rng.randrange(n_items)
        length = max(1, min(n_periods, int(round(strength)) + 1))
        start = rng.randrange(n_periods)
        for dt in range(length):
            t = (start + dt) % n_periods
            s[i0][t] = True

        out = self.problem.parts.canonical(tuple(tuple(row) for row in s))
        if out == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s[i][t] = not s[i][t]
            out = self.problem.parts.canonical(tuple(tuple(row) for row in s))
        return out


def build_component(problem, **params):
    ruin_fraction = params.get("ruin_fraction", 0.2)
    return BiasedRuinAndRepairKick(problem, ruin_fraction=ruin_fraction)
