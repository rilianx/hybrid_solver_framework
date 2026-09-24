from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import Solution

COMPONENT = {
    "name": "item_chain_shift_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "int", "range": [1, 10]},
    },
}


class ItemChainShiftKick:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst = problem.inst

    def perturb(self, sol: Solution, strength: float, rng: Random) -> Solution:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        if n_items <= 0 or n_periods <= 0:
            return sol

        m = int(round(strength))
        if m < 1:
            m = 1
        if m > 10:
            m = 10

        rows = [list(row) for row in sol]

        # Prefer an item that already has setups; otherwise any item.
        items_with_setups = [i for i in range(n_items) if any(rows[i])]
        if items_with_setups:
            i = items_with_setups[rng.randrange(len(items_with_setups))]
        else:
            i = rng.randrange(n_items)

        row = rows[i]

        # The stronger the kick, the more elementary item-local temporal moves are applied.
        # Each move is a single-step chain shift / local toggle, focused on one item.
        for _ in range(m):
            setup_positions = [t for t, v in enumerate(row) if v]

            if not setup_positions:
                # Seed a setup if the item is empty.
                t = rng.randrange(n_periods)
                row[t] = True
                continue

            center = setup_positions[rng.randrange(len(setup_positions))]

            # Bias the direction so that repeated operations tend to spread the chain,
            # rather than canceling each other out.
            if center == 0:
                direction = 1
            elif center == n_periods - 1:
                direction = -1
            else:
                direction = 1 if rng.random() < 0.5 else -1

            # Elementary one-period shift of a single setup bit.
            target = center + direction
            if 0 <= target < n_periods:
                if row[center] and not row[target]:
                    row[center] = False
                    row[target] = True
                elif row[center] and row[target]:
                    # If the target is already active, push the chain locally by toggling
                    # a neighboring period to keep the move item-focused and nontrivial.
                    spill = target + direction
                    if 0 <= spill < n_periods:
                        row[spill] = not row[spill]
                    else:
                        row[center] = not row[center]
                else:
                    row[target] = not row[target]
            else:
                # Boundary fallback: toggle the selected setup to guarantee a change.
                row[center] = not row[center]

        rows[i] = row
        cand = tuple(tuple(r) for r in rows)

        if cand != sol:
            return cand

        # Guaranteed fallback: flip one bit in the chosen item.
        fallback_rows = [list(row) for row in sol]
        t = rng.randrange(n_periods)
        fallback_rows[i][t] = not fallback_rows[i][t]
        cand = tuple(tuple(r) for r in fallback_rows)
        if cand != sol:
            return cand

        return sol


def build_component(problem, **params):
    return ItemChainShiftKick(problem)
