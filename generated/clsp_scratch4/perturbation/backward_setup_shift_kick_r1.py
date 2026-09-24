from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel


COMPONENT = {
    "name": "backward_setup_shift_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 6.0]}},
}


class BackwardSetupShiftKick:
    def __init__(self, problem: LotSizingModel):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    @staticmethod
    def _copy(sol):
        return tuple(tuple(row) for row in sol)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        y = [list(row) for row in sol]
        k = max(1, int(round(strength)))

        # Candidate moves: shift a setup one period earlier for items that
        # already have a setup in the previous period, or create one earlier if
        # it helps to merge demand blocks.
        candidates = []
        for i in range(n_items):
            on = [t for t in range(n_periods) if y[i][t]]
            for t in on:
                if t > 0 and not y[i][t - 1]:
                    candidates.append((i, t, t - 1))
                if t + 1 < n_periods and not y[i][t + 1]:
                    candidates.append((i, t, t + 1))

        if not candidates:
            # Guaranteed change: flip a random bit and then repair by adding one
            # more setup of the same item if needed.
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            y[i][t] = not y[i][t]
            if not y[i][t]:
                alt = (t + 1) % n_periods
                y[i][alt] = True
            return tuple(tuple(row) for row in y)

        rng.shuffle(candidates)
        moved = 0
        for i, t_from, t_to in candidates:
            if moved >= k:
                break
            # Shift one setup earlier/later; never remove the only setup of an item.
            setup_count = sum(y[i])
            if setup_count <= 1:
                continue
            y[i][t_from] = False
            y[i][t_to] = True
            moved += 1

        if moved == 0:
            i, t_from, t_to = candidates[0]
            y[i][t_from] = False
            y[i][t_to] = True

        out = tuple(tuple(row) for row in y)
        if out == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            row = list(out[i])
            row[t] = not row[t]
            if not any(row):
                row[(t + 1) % n_periods] = True
            out = tuple(tuple(row) if j == i else out[j] for j in range(n_items))
        return out


def build_component(problem, **params):
    strength = params.get("strength", 2.0)
    return BackwardSetupShiftKick(problem)
