from __future__ import annotations

from random import Random
from typing import Any
from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "capacity_pressure_window_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 6.0]},
    },
}


class CapacityPressureWindowKick:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    def _period_pressure(self, sol) -> list[float]:
        inst = self.inst
        pressures: list[float] = []
        for t in range(inst.n_periods):
            used = 0.0
            for i in range(inst.n_items):
                if sol[i][t]:
                    used += inst.setup_time[i] + inst.demand[i][t]
            cap = inst.capacity[t]
            pressures.append(used / cap if cap > 1e-12 else float("inf"))
        return pressures

    def _choose_window(self, pressures: list[float], strength: float, rng: Random) -> tuple[int, int]:
        n = len(pressures)
        if n == 1:
            return 0, 1
        win_len = max(2, min(n, int(round(1.0 + strength / 2.0))))
        best_score = None
        best_starts: list[int] = []
        for s in range(0, n - win_len + 1):
            score = sum(pressures[s : s + win_len]) / win_len
            if best_score is None or score > best_score + 1e-12:
                best_score = score
                best_starts = [s]
            elif abs(score - best_score) <= 1e-12:
                best_starts.append(s)
        start = rng.choice(best_starts)
        return start, start + win_len

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        pressures = self._period_pressure(sol)
        start, end = self._choose_window(pressures, max(1.0, strength), rng)

        # Build candidate setups inside the congested window.
        candidates = []
        for i in range(inst.n_items):
            for t in range(start, end):
                if sol[i][t]:
                    future_demand = sum(inst.demand[i][tt] for tt in range(t + 1, end))
                    # Lower score => more disposable setup.
                    score = inst.setup_cost[i] - 0.5 * future_demand - 0.1 * inst.holding_cost[i] * future_demand
                    candidates.append((score, i, t))

        if not candidates:
            # Fallback: remove setups from the most pressured period.
            t = max(range(inst.n_periods), key=lambda tt: pressures[tt])
            candidates = []
            for i in range(inst.n_items):
                if sol[i][t]:
                    score = inst.setup_cost[i] - 0.1 * inst.holding_cost[i] * inst.demand[i][t]
                    candidates.append((score, i, t))
            if not candidates:
                # Absolute fallback: flip any setup if the solution is degenerate.
                for i in range(inst.n_items):
                    for t in range(inst.n_periods):
                        if sol[i][t]:
                            candidates.append((0.0, i, t))
                            break
                    if candidates:
                        break

        if not candidates:
            return sol

        candidates.sort(key=lambda x: (x[0], rng.random()))
        max_k = max(1, int(round(strength)))
        k = min(len(candidates), max_k)

        # Favor destroying low-utility setups in the congested window.
        selected = candidates[:k]
        new_sol = [list(row) for row in sol]
        changed = False
        for _, i, t in selected:
            if new_sol[i][t]:
                new_sol[i][t] = False
                changed = True

        if not changed:
            # Guaranteed distinctness: flip one candidate off, or if impossible, a random setup.
            _, i, t = rng.choice(candidates)
            new_sol[i][t] = not new_sol[i][t]
            changed = True

        return tuple(tuple(row) for row in new_sol)


def build_component(problem, **params):
    strength = params.get("strength", 2.0)
    return CapacityPressureWindowKick(problem)
