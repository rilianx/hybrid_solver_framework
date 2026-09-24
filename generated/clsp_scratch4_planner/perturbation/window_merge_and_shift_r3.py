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
        base = max(2.0, self.window_ratio * n_periods)
        window_len = int(round(base + 0.75 * strength))
        window_len = max(2, min(n_periods, window_len))
        if window_len >= n_periods:
            return 0, n_periods - 1
        a = rng.randrange(0, n_periods - window_len + 1)
        return a, a + window_len - 1

    def _build_candidates(self, sol, a: int, b: int):
        n_items = self.inst.n_items
        candidates = []
        for i in range(n_items):
            on = [t for t in range(a, b + 1) if sol[i][t]]
            if len(on) >= 2:
                # Prefer merging late setups into earlier ones inside the window.
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
        return candidates

    def _apply_move(self, sol, move):
        i, t1, t2, kind = move
        rows = [list(r) for r in sol]
        if kind == "merge":
            rows[i][t2] = False
        elif kind == "shift_left":
            rows[i][t2] = False
            rows[i][t1] = True
        else:  # shift_right
            rows[i][t1] = False
            rows[i][t2] = True
        cand = tuple(tuple(r) for r in rows)
        return cand if cand != sol else None

    def _single_local_move(self, sol, a: int, b: int, rng: Random):
        candidates = self._build_candidates(sol, a, b)
        if not candidates:
            return None

        # Preserve the original idea: bias toward merge moves, but keep elementary.
        merge_moves = [m for m in candidates if m[3] == "merge"]
        shift_moves = [m for m in candidates if m[3] != "merge"]

        if merge_moves and rng.random() < self.merge_bias:
            move = merge_moves[rng.randrange(len(merge_moves))]
        else:
            move = candidates[rng.randrange(len(candidates))]

        return self._apply_move(sol, move)

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

        # Monotone kick strength: larger strength => more successful elementary moves.
        n_moves = max(1, min(1 + int(round(strength)), 8))
        n_windows = max(1, min(self.attempts, 1 + int(round(strength))))

        best = None

        for _ in range(n_windows):
            current = base
            changed = False

            for _ in range(n_moves):
                a, b = self._window_bounds(n_periods, strength, rng)
                cand = self._single_local_move(current, a, b, rng)
                if cand is None or cand == current:
                    continue
                current = cand
                changed = True

            if changed and current != sol:
                best = current
                break

        if best is not None and best != sol:
            return best

        return self._fallback_flip(sol)


def build_component(problem, **params):
    window_ratio = params.get("window_ratio", 0.25)
    attempts = params.get("attempts", 4)
    merge_bias = params.get("merge_bias", 0.85)
    return WindowMergeAndShift(problem, window_ratio=window_ratio, attempts=attempts, merge_bias=merge_bias)
