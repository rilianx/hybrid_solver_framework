from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import LotSizingModel, CLSPInstance


COMPONENT = {
    "name": "block_shift_item_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "window": {"type": "int", "range": [1, 6]},
        "direction_bias": {"type": "cat", "values": ["random", "earlier", "later"]},
    },
}


class BlockShiftItemPerturbation:
    def __init__(self, problem: LotSizingModel, window: int = 2, direction_bias: str = "random"):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.window = window
        self.direction_bias = direction_bias

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        i = rng.randrange(n_items)
        row = list(sol[i])

        ones = [t for t, v in enumerate(row) if v]
        if not ones:
            # Fallback: create one setup to ensure a distinct solution.
            t = rng.randrange(n_periods)
            row[t] = True
            new_sol = list(list(r) for r in sol)
            new_sol[i] = tuple(row)
            return tuple(new_sol)

        w = max(1, min(self.window, int(round(strength))))
        if len(ones) <= w:
            start_idx = 0
        else:
            start_idx = rng.randrange(0, len(ones) - w + 1)
        block = ones[start_idx : start_idx + w]

        if self.direction_bias == "random":
            direction = -1 if rng.random() < 0.5 else 1
        elif self.direction_bias == "earlier":
            direction = -1
        else:
            direction = 1

        # Try to shift the whole block by one period; if that is impossible,
        # fall back to a local rewire inside the block window.
        candidate = row[:]
        shifted = []
        feasible_shift = True
        for t in block:
            nt = t + direction
            if nt < 0 or nt >= n_periods:
                feasible_shift = False
                break
            shifted.append(nt)

        if feasible_shift:
            for t in block:
                candidate[t] = False
            for nt in shifted:
                candidate[nt] = True
            if tuple(candidate) != sol[i]:
                new_sol = list(list(r) for r in sol)
                new_sol[i] = tuple(candidate)
                return tuple(new_sol)

        # Local fallback: move the block one period toward the chosen direction
        # by reassigning each True to a nearby period, keeping the row distinct.
        candidate = row[:]
        changed = False
        for t in block:
            candidate[t] = False
            nt = min(max(t + direction, 0), n_periods - 1)
            if nt != t:
                candidate[nt] = True
                changed = True
        if not changed:
            # force a difference
            t = rng.choice(block)
            nt = (t + 1) % n_periods
            candidate[t] = False
            candidate[nt] = True

        new_sol = list(list(r) for r in sol)
        new_sol[i] = tuple(candidate)
        return tuple(new_sol)


def build_component(problem, **params):
    return BlockShiftItemPerturbation(
        problem,
        window=int(params.get("window", 2)),
        direction_bias=str(params.get("direction_bias", "random")),
    )
