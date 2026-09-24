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
        inst = self.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        k = max(1, min(n_periods - 1 if n_periods > 1 else 1, int(round(strength))))

        item_order = list(range(n_items))
        rng.shuffle(item_order)

        def shifted_row(row: tuple[bool, ...], a: int, b: int, direction: int) -> tuple[bool, ...]:
            new_row = list(row)
            if direction > 0:
                for t in range(b, a, -1):
                    new_row[t] = row[t - 1]
                new_row[a] = False
            else:
                for t in range(a, b):
                    new_row[t] = row[t + 1]
                new_row[b] = False
            return tuple(new_row)

        best_candidate = None
        best_obj = None

        for i in item_order[: min(n_items, max(1, k))]:
            row = sol[i]
            trues = [t for t, v in enumerate(row) if v]
            if not trues:
                continue

            # Select a focused window around an existing setup chain.
            center = trues[rng.randrange(len(trues))]
            half = max(1, min(k, n_periods - 1) // 2)
            a = max(0, center - half)
            b = min(n_periods - 1, a + max(1, min(k, n_periods - 1)))
            a = max(0, b - max(1, min(k, n_periods - 1)))

            # If the window is too short, expand when possible.
            if a == b and n_periods > 1:
                if b < n_periods - 1:
                    b += 1
                else:
                    a -= 1

            candidates = []
            if b > a:
                candidates.append(shifted_row(row, a, b, +1))
                candidates.append(shifted_row(row, a, b, -1))
            else:
                candidates.append(tuple(not row[t] if t == center else row[t] for t in range(n_periods)))

            for new_row in candidates:
                if new_row == row:
                    continue
                new_sol = list(sol)
                new_sol[i] = new_row
                cand = tuple(new_sol)
                obj = self.problem.objective(cand)
                if best_candidate is None or obj < best_obj:
                    best_candidate = cand
                    best_obj = obj

            # With enough strength, try a second item to make the kick more disruptive.
            if k >= 3 and len(item_order) > 1:
                j = item_order[(item_order.index(i) + 1) % len(item_order)]
                if j != i:
                    row2 = sol[j]
                    trues2 = [t for t, v in enumerate(row2) if v]
                    if trues2:
                        center2 = trues2[rng.randrange(len(trues2))]
                        a2 = max(0, center2 - 1)
                        b2 = min(n_periods - 1, center2 + 1)
                        for direction in (+1, -1):
                            new_row2 = shifted_row(row2, a2, b2, direction) if b2 > a2 else tuple(
                                not row2[t] if t == center2 else row2[t] for t in range(n_periods)
                            )
                            if new_row2 == row2:
                                continue
                            new_sol = list(sol)
                            new_sol[i] = best_candidate[i] if best_candidate is not None else new_sol[i]
                            new_sol[j] = new_row2
                            cand = tuple(new_sol)
                            obj = self.problem.objective(cand)
                            if best_candidate is None or obj < best_obj:
                                best_candidate = cand
                                best_obj = obj

        if best_candidate is not None and best_candidate != sol:
            return best_candidate

        # Guaranteed change fallback: flip one setup bit in a random item/period.
        i = rng.randrange(n_items)
        t = rng.randrange(n_periods)
        new_sol = [list(row) for row in sol]
        new_sol[i][t] = not new_sol[i][t]
        cand = tuple(tuple(row) for row in new_sol)
        if cand != sol:
            return cand

        # Final fallback: flip the first bit.
        new_sol = [list(row) for row in sol]
        new_sol[0][0] = not new_sol[0][0]
        return tuple(tuple(row) for row in new_sol)


def build_component(problem, **params):
    strength = params.get("strength", 3)
    if not (1 <= int(round(strength)) <= 10):
        strength = 3
    return ItemChainShiftKick(problem)
