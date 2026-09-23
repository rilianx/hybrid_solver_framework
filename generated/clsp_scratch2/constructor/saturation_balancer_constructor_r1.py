from __future__ import annotations

from random import Random
from typing import Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "saturation_balancer_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "balance_strength": {"type": "float", "range": [0.0, 3.0]},
        "shake_steps": {"type": "int", "range": [1, 40]},
    },
}


class SaturationBalancerConstructor:
    """Constructor basado en balanceo de saturación: empieza con lot-for-lot y reubica setups desde períodos congestivos."""

    def __init__(self, problem: LotSizingModel, balance_strength: float = 1.2, shake_steps: int = 15):
        self.problem = problem
        self.balance_strength = balance_strength
        self.shake_steps = shake_steps

    def _empty_sol(self, inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int, value: bool):
        return tuple(
            tuple(value if (ii == i and tt == t) else sol[ii][tt] for tt in range(len(sol[0])))
            for ii in range(len(sol))
        )

    def _period_loads(self, sol, inst):
        return [sum(inst.setup_time[i] for i in range(inst.n_items) if sol[i][t]) for t in range(inst.n_periods)]

    def _initial_lot_for_lot(self, inst: CLSPInstance, rng: Random):
        n, T = inst.n_items, inst.n_periods
        sol = self._empty_sol(inst)
        for i in range(n):
            for t in range(T):
                if inst.demand[i][t] > 0:
                    sol = self._set(sol, i, t, True)
            # Small random spreading for items with very low holding cost.
            if T > 1 and inst.holding_cost[i] <= 2 and rng.random() < 0.4:
                sol = self._set(sol, i, 0, True)
        return sol

    def build(self, inst: CLSPInstance, rng: Random):
        sol = self._initial_lot_for_lot(inst, rng)
        if self.problem.is_feasible(sol):
            return sol

        n, T = inst.n_items, inst.n_periods
        for _ in range(self.shake_steps):
            if self.problem.is_feasible(sol):
                return sol

            loads = self._period_loads(sol, inst)
            congested = max(range(T), key=lambda t: loads[t] / max(inst.capacity[t], 1e-9))
            relaxed = min(range(T), key=lambda t: loads[t] / max(inst.capacity[t], 1e-9))

            # Candidate moves: move a setup away from congestion to a lighter period.
            best = None
            for i in range(n):
                if not sol[i][congested]:
                    continue
                for tt in range(T):
                    if tt == congested or sol[i][tt]:
                        continue
                    # Prefer moving to earlier light periods if we are in a backlog-sensitive zone.
                    score = (
                        (inst.capacity[tt] - loads[tt]) * self.balance_strength
                        + (congested - tt if tt < congested else -1.0)
                        - inst.holding_cost[i]
                        + rng.random() * 0.01
                    )
                    cand = (score, i, tt)
                    if best is None or cand > best:
                        best = cand

            if best is None:
                # If no move is possible, add a setup to the most relaxed period for a high-demand item.
                items = sorted(range(n), key=lambda i: (-sum(inst.demand[i]), inst.holding_cost[i], rng.random()))
                moved = False
                for i in items:
                    if not sol[i][relaxed]:
                        sol = self._set(sol, i, relaxed, True)
                        moved = True
                        break
                if not moved:
                    break
            else:
                _, i, tt = best
                sol = self._set(sol, i, tt, True)

        if self.problem.is_feasible(sol):
            return sol

        # Conservative finishing phase: ensure every positive-demand cell has a setup.
        for i in range(n):
            for t in range(T):
                if inst.demand[i][t] > 0 and not sol[i][t]:
                    sol = self._set(sol, i, t, True)
        return sol


def build_component(problem, balance_strength: float = 1.2, shake_steps: int = 15):
    return SaturationBalancerConstructor(problem, balance_strength=balance_strength, shake_steps=shake_steps)
