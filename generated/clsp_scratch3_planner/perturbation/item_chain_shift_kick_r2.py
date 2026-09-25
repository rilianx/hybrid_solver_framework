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

        def as_list_solution(s: Solution) -> list[list[bool]]:
            return [list(row) for row in s]

        def to_solution(rows: list[list[bool]]) -> Solution:
            return tuple(tuple(row) for row in rows)

        def shift_segment(row: list[bool], a: int, b: int, direction: int) -> list[bool]:
            # Shift the contiguous segment [a, b] one position in the given direction,
            # keeping the modification focused on the same item.
            new_row = row[:]
            if direction > 0:
                # [a..b] -> [a+1..b+1], if room exists
                for t in range(b, a - 1, -1):
                    if t + 1 < n_periods:
                        new_row[t + 1] = row[t]
                if a < n_periods:
                    new_row[a] = False
            else:
                # [a..b] -> [a-1..b-1], if room exists
                for t in range(a, b + 1):
                    if t - 1 >= 0:
                        new_row[t - 1] = row[t]
                if b >= 0:
                    new_row[b] = False
            return new_row

        rows = as_list_solution(sol)

        # Prefer an item with existing setups; otherwise any item.
        items_with_setups = [i for i in range(n_items) if any(rows[i])]
        if items_with_setups:
            i = items_with_setups[rng.randrange(len(items_with_setups))]
        else:
            i = rng.randrange(n_items)

        row = rows[i]
        setup_positions = [t for t, v in enumerate(row) if v]

        # Apply a number of elementary item-local kicks proportional to strength.
        # Stronger kicks perform more local temporal moves on the same item.
        for step in range(m):
            if not any(row):
                t = rng.randrange(n_periods)
                row[t] = True
                continue

            setup_positions = [t for t, v in enumerate(row) if v]
            center = setup_positions[rng.randrange(len(setup_positions))]

            # Local window size grows mildly with strength.
            radius = min(n_periods - 1, max(1, m // 3))
            a = max(0, center - radius)
            b = min(n_periods - 1, center + radius)

            # Alternate between shifting a local chain and toggling one boundary bit.
            if b > a and (step % 2 == 0 or m == 1):
                direction = 1 if rng.random() < 0.5 else -1
                candidate = shift_segment(row, a, b, direction)
                if candidate != row:
                    row = candidate
                else:
                    # Fallback: toggle a nearby bit to guarantee change.
                    t = center
                    if direction > 0 and center + 1 < n_periods:
                        t = center + 1
                    elif direction < 0 and center - 1 >= 0:
                        t = center - 1
                    row[t] = not row[t]
            else:
                # Split or merge locally by toggling a neighboring period.
                if center + 1 < n_periods and (not row[center + 1] or m >= 4):
                    row[center + 1] = not row[center + 1]
                elif center - 1 >= 0:
                    row[center - 1] = not row[center - 1]
                else:
                    row[center] = not row[center]

        rows[i] = row
        cand = to_solution(rows)

        if cand != sol:
            return cand

        # Last-resort guaranteed change: flip one setup bit in the chosen item.
        fallback_rows = as_list_solution(sol)
        t = rng.randrange(n_periods)
        fallback_rows[i][t] = not fallback_rows[i][t]
        cand = to_solution(fallback_rows)
        if cand != sol:
            return cand

        # If n_periods == 0 or some degenerate case, return original.
        return sol


def build_component(problem, **params):
    strength = params.get("strength", 3)
    try:
        strength = int(round(strength))
    except Exception:
        strength = 3
    if strength < 1:
        strength = 1
    if strength > 10:
        strength = 10
    return ItemChainShiftKick(problem)
