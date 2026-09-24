from __future__ import annotations

from random import Random
from typing import Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "period_first_slack_packer",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "prefer_early": {"type": "bool", "values": [True, False]},
        "slack_margin": {"type": "float", "range": [0.0, 0.3]},
    },
}


class PeriodFirstSlackPacker:
    """Constructor por períodos: llena la capacidad con un empaquetado por prefijos y repara con setups adicionales."""

    def __init__(self, problem: LotSizingModel, prefer_early: bool = True, slack_margin: float = 0.1):
        self.problem = problem
        self.prefer_early = prefer_early
        self.slack_margin = slack_margin

    def _initial(self, inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        n, m = inst.n_items, inst.n_periods
        sol = [[False] * m for _ in range(n)]
        cap = list(inst.capacity)
        # Empaqueta por períodos; los ítems con mayor "presión" se abren antes.
        for t in range(m):
            pressure = []
            for i in range(n):
                future = sum(inst.demand[i][tt] for tt in range(t, m))
                if future > 0:
                    score = (future + inst.setup_cost[i]) / (1.0 + inst.holding_cost[i])
                    if not self.prefer_early:
                        score = future / (1.0 + inst.setup_time[i])
                    pressure.append((score, i))
            pressure.sort(reverse=True)
            used = 0.0
            for _, i in pressure:
                if used + inst.setup_time[i] <= cap[t] * (1.0 - self.slack_margin):
                    sol[i][t] = True
                    used += inst.setup_time[i]
            # Si un período queda demasiado vacío y hay demanda en el horizonte, añade algunos setups
            if used < 1e-9 and pressure:
                i = pressure[0][1]
                if inst.setup_time[i] <= cap[t]:
                    sol[i][t] = True
        return tuple(tuple(r) for r in sol)

    def _densify(self, inst: CLSPInstance, sol: Tuple[Tuple[bool, ...], ...]) -> Tuple[Tuple[bool, ...], ...]:
        if self.problem.is_feasible(sol):
            return sol
        n, m = inst.n_items, inst.n_periods
        cur = [list(r) for r in sol]
        # Agrega setups en períodos con más holgura primero
        for _ in range(n * m):
            trial = tuple(tuple(r) for r in cur)
            if self.problem.is_feasible(trial):
                return trial
            best = None
            best_gain = -1e18
            for t in range(m):
                slack = inst.capacity[t] - sum(inst.setup_time[i] for i in range(n) if cur[i][t])
                if slack <= 0:
                    continue
                for i in range(n):
                    if cur[i][t] or inst.setup_time[i] > slack:
                        continue
                    future_d = sum(inst.demand[i][tt] for tt in range(t, m))
                    if future_d <= 0:
                        continue
                    gain = future_d - 0.1 * inst.setup_cost[i] - 0.05 * inst.holding_cost[i] * t
                    if gain > best_gain:
                        best_gain = gain
                        best = (i, t)
            if best is None:
                # fallback: activa el primer setup factible encontrado
                found = False
                for t in range(m):
                    for i in range(n):
                        if not cur[i][t]:
                            slack = inst.capacity[t] - sum(inst.setup_time[k] for k in range(n) if cur[k][t])
                            if slack >= inst.setup_time[i]:
                                cur[i][t] = True
                                found = True
                                break
                    if found:
                        break
                if not found:
                    break
            else:
                i, t = best
                cur[i][t] = True
        return tuple(tuple(r) for r in cur)

    def build(self, inst: CLSPInstance, rng: Random):
        sol = self._initial(inst)
        sol = self._densify(inst, sol)
        if self.problem.is_feasible(sol):
            return sol
        # Reparación final monotónica: añadir setups por orden de mayor capacidad libre.
        cur = [list(r) for r in sol]
        for t in range(inst.n_periods):
            for i in range(inst.n_items):
                if not cur[i][t]:
                    cur[i][t] = True
                    trial = tuple(tuple(r) for r in cur)
                    if self.problem.is_feasible(trial):
                        return trial
        return tuple(tuple(r) for r in cur)


def build_component(problem, prefer_early: bool = True, slack_margin: float = 0.1):
    return PeriodFirstSlackPacker(problem, prefer_early=prefer_early, slack_margin=slack_margin)
