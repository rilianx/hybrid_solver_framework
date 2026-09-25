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

    def _mutate_window(self, sol, a: int, b: int, rng: Random):
        inst = self.inst
        n_items = inst.n_items

        candidates = []
        for i in range(n_items):
            on = [t for t in range(a, b + 1) if sol[i][t]]
            if len(on) >= 2:
                for later in on[1:]:
                    earlier = [t for t in on if t < later]
                    if earlier:
                        candidates.append((i, earlier[-1], later, "merge"))
            elif len(on) == 1:
                t = on[0]
                if t > a:
                    candidates.append((i, t - 1, t, "shift_left"))
                if t < b:
                    candidates.append((i, t, t + 1, "shift_right"))

        if not candidates:
            return None

        i, t1, t2, kind = candidates[rng.randrange(len(candidates))]

        rows = [list(r) for r in sol]
        changed = False

        if kind == "merge":
            # Fuse: apagamos el setup tardío, dejando que el LP replantee cantidades.
            if rows[i][t2]:
                rows[i][t2] = False
                changed = True
            else:
                return None
        elif kind == "shift_left":
            # Desplazamiento local: mover un setup una posición antes dentro de la ventana.
            if rows[i][t2] and not rows[i][t1]:
                rows[i][t2] = False
                rows[i][t1] = True
                changed = True
            elif rows[i][t2]:
                # Si el período anterior ya está activo, preferimos fusionar apagando el tardío.
                rows[i][t2] = False
                changed = True
        else:  # shift_right
            if rows[i][t1] and not rows[i][t2]:
                rows[i][t1] = False
                rows[i][t2] = True
                changed = True
            elif rows[i][t1]:
                rows[i][t1] = False
                changed = True

        if not changed:
            return None

        return tuple(tuple(r) for r in rows)

    def perturb(self, sol, strength: float, rng: Random):
        n_periods = self.inst.n_periods
        if n_periods <= 1:
            # Distinta de sol para strength>=1: voltear el único setup posible del primer ítem.
            rows = [list(r) for r in sol]
            rows[0][0] = not rows[0][0]
            return tuple(tuple(r) for r in rows)

        base = self._copy_sol(sol)
        k = max(1, int(round(strength)))
        window_len = max(2, min(n_periods, int(round(2 + self.window_ratio * n_periods + 0.5 * k))))
        n_windows = max(1, min(self.attempts, k + 1))

        best = None
        best_obj = None

        for _ in range(n_windows):
            if window_len >= n_periods:
                a, b = 0, n_periods - 1
            else:
                a = rng.randrange(0, n_periods - window_len + 1)
                b = a + window_len - 1

            cand = self._mutate_window(base, a, b, rng)
            if cand is None or cand == sol:
                continue

            # A veces encadenamos 1-2 movimientos locales dentro de la misma ventana.
            extra_moves = 1 if (k > 1 and rng.random() < self.merge_bias) else 0
            current = cand
            for _m in range(extra_moves):
                cand2 = self._mutate_window(current, a, b, rng)
                if cand2 is not None and cand2 != current:
                    current = cand2

            cand = current
            try:
                obj = self.problem.objective(cand)
            except Exception:
                obj = None

            if best is None:
                best, best_obj = cand, obj
            elif obj is not None and (best_obj is None or obj < best_obj):
                best, best_obj = cand, obj

        if best is not None and best != sol:
            return best

        # Fallback garantizado: modificación mínima pero distinta.
        rows = [list(r) for r in sol]
        for i in range(self.inst.n_items):
            for t in range(n_periods - 1, -1, -1):
                if rows[i][t]:
                    rows[i][t] = False
                    return tuple(tuple(r) for r in rows)

        # Si todo estaba apagado, enciende una celda.
        rows[0][0] = True
        return tuple(tuple(r) for r in rows)


def build_component(problem, **params):
    window_ratio = params.get("window_ratio", 0.25)
    attempts = params.get("attempts", 4)
    merge_bias = params.get("merge_bias", 0.85)
    return WindowMergeAndShift(problem, window_ratio=window_ratio, attempts=attempts, merge_bias=merge_bias)
