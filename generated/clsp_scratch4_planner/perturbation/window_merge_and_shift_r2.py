from __future__ import annotations

from random import Random
from typing import Any


COMPONENT = {
    "name": "window_merge_and_shift",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "window_ratio": {"type": "float", "range": [0.10, 0.50]},
        "attempts": {"type": "int", "range": [1, 12]},
        "merge_bias": {"type": "float", "range": [0.50, 1.00]},
    },
}


class WindowMergeAndShift:
    def __init__(self, problem: Any, window_ratio: float = 0.25, attempts: int = 4, merge_bias: float = 0.85):
        self.problem = problem
        self.inst = problem.inst
        self.window_ratio = float(window_ratio)
        self.attempts = int(attempts)
        self.merge_bias = float(merge_bias)

    def _copy_sol(self, sol):
        return tuple(tuple(row) for row in sol)

    def _window_bounds(self, n_periods: int, strength: float, rng: Random):
        base = 2 + self.window_ratio * n_periods
        # Strength increases window size to encourage larger local restructuring.
        window_len = int(round(base + strength))
        window_len = max(2, min(n_periods, window_len))
        if window_len >= n_periods:
            return 0, n_periods - 1
        a = rng.randrange(0, n_periods - window_len + 1)
        return a, a + window_len - 1

    def _single_local_move(self, sol, a: int, b: int, rng: Random):
        n_items = self.inst.n_items
        candidates = []

        for i in range(n_items):
            on = [t for t in range(a, b + 1) if sol[i][t]]
            if len(on) >= 2:
                # Merge-like move: choose a later setup and remove it if an earlier one exists.
                for later in on[1:]:
                    earlier = [t for t in on if t < later]
                    if earlier:
                        candidates.append((i, earlier[-1], later, "merge"))
            elif len(on) == 1:
                t = on[0]
                if t > a and not sol[i][t - 1]:
                    candidates.append((i, t - 1, t, "shift_left"))
                if t < b and not sol[i][t + 1]:
                    candidates.append((i, t, t + 1, "shift_right"))

        if not candidates:
            return None

        i, t1, t2, kind = candidates[rng.randrange(len(candidates))]
        rows = [list(r) for r in sol]

        if kind == "merge":
            # Elementary move: drop the late setup, letting the LP rebalance quantities/inventory.
            rows[i][t2] = False
        elif kind == "shift_left":
            # Elementary move: move one setup one period earlier inside the window.
            rows[i][t2] = False
            rows[i][t1] = True
        else:  # shift_right
            # Elementary move: move one setup one period later inside the window.
            rows[i][t1] = False
            rows[i][t2] = True

        cand = tuple(tuple(r) for r in rows)
        return cand if cand != sol else None

    def _fallback_flip(self, sol):
        rows = [list(r) for r in sol]
        for i in range(self.inst.n_items):
            for t in range(self.inst.n_periods - 1, -1, -1):
                rows[i][t] = not rows[i][t]
                return tuple(tuple(r) for r in rows)
        rows[0][0] = True
        return tuple(tuple(r) for r in rows)

    def perturb(self, sol, strength: float, rng: Random):
        n_periods = self.inst.n_periods
        if n_periods <= 1:
            return self._fallback_flip(sol)

        base = self._copy_sol(sol)

        # More strength => more elementary local moves.
        n_steps = max(1, min(6, int(round(1 + strength))))
        n_windows = max(1, min(self.attempts, int(round(1 + strength))))

        best = None
        best_obj = None

        for _ in range(n_windows):
            current = base
            changed = False

            for _s in range(n_steps):
                a, b = self._window_bounds(n_periods, strength, rng)
                cand = self._single_local_move(current, a, b, rng)
                if cand is None or cand == current:
                    continue
                current = cand
                changed = True

            if not changed or current == sol:
                continue

            try:
                obj = self.problem.objective(current)
            except Exception:
                obj = None

            if best is None:
                best, best_obj = current, obj
            elif obj is not None and (best_obj is None or obj < best_obj):
                best, best_obj = current, obj

        if best is not None and best != sol:
            return best

        return self._fallback_flip(sol)


def build_component(problem, **params):
    window_ratio = params.get("window_ratio", 0.25)
    attempts = params.get("attempts", 4)
    merge_bias = params.get("merge_bias", 0.85)
    return WindowMergeAndShift(problem, window_ratio=window_ratio, attempts=attempts, merge_bias=merge_bias)
