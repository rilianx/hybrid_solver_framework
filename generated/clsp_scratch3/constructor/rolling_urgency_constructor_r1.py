from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "rolling_urgency_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "lookahead": {"type": "int", "range": [1, 8]},
        "slack_bias": {"type": "float", "range": [0.0, 2.0]},
    },
}


class RollingUrgencyConstructor:
    """Constructor secuencial: abre setups cuando la demanda futura acumulada supera la holgura esperada."""

    def __init__(self, lookahead: int = 3, slack_bias: float = 0.8):
        self.lookahead = lookahead
        self.slack_bias = slack_bias

    def _empty(self, inst):
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int):
        row = list(sol[i])
        row[t] = True
        return sol[:i] + (tuple(row),) + sol[i + 1 :]

    def _interval_need(self, inst, i: int, t: int) -> float:
        end = min(inst.n_periods, t + self.lookahead)
        return sum(inst.demand[i][tt] for tt in range(t, end))

    def _repair(self, problem, sol, rng: Random):
        inst = problem.inst
        for _ in range(inst.n_items * inst.n_periods * 3):
            if problem.is_feasible(sol):
                return sol
            best = None
            best_score = None
            for i in range(inst.n_items):
                for t in range(inst.n_periods):
                    if sol[i][t]:
                        continue
                    future = self._interval_need(inst, i, t)
                    score = (future / (1.0 + inst.setup_time[i])) + self.slack_bias * inst.holding_cost[i]
                    if best_score is None or score > best_score or (score == best_score and rng.random() < 0.5):
                        best_score = score
                        best = (i, t)
            if best is None:
                break
            sol = self._set(sol, best[0], best[1])
        return sol

    def build(self, inst, rng: Random):
        periods = list(range(inst.n_periods))
        sol = self._empty(inst)

        remaining_prefix = [0.0] * inst.n_periods
        acc = 0.0
        for t in range(inst.n_periods):
            acc += sum(inst.demand[i][t] for i in range(inst.n_items))
            remaining_prefix[t] = acc

        order = sorted(
            range(inst.n_items),
            key=lambda i: (inst.holding_cost[i] / (1.0 + inst.setup_cost[i]), -sum(inst.demand[i])),
        )

        for t in periods:
            cap = inst.capacity[t]
            used_setup = 0.0
            chosen: List[int] = []
            candidates = [i for i in order if inst.demand[i][t] > 0 or self._interval_need(inst, i, t) > 0]
            candidates.sort(
                key=lambda i: (
                    -self._interval_need(inst, i, t) / (1.0 + inst.setup_time[i]),
                    inst.setup_time[i],
                    rng.random(),
                )
            )
            for i in candidates:
                if not sol[i][t]:
                    if used_setup + inst.setup_time[i] <= cap * 0.7:
                        sol = self._set(sol, i, t)
                        used_setup += inst.setup_time[i]
                        chosen.append(i)

            # If the period is still very light and there is future demand, add a few proactive setups.
            if used_setup < cap * 0.4:
                extras = [i for i in order if not sol[i][t]]
                extras.sort(key=lambda i: (-self._interval_need(inst, i, t + 1), inst.setup_time[i], rng.random()))
                for i in extras:
                    if used_setup + inst.setup_time[i] <= cap * 0.85:
                        sol = self._set(sol, i, t)
                        used_setup += inst.setup_time[i]

        sol = self._repair(problem=__import__("examples.lotsizing.problem_model", fromlist=["LotSizingModel"]), sol=sol, rng=rng)
        return sol


def build_component(problem, lookahead: int = 3, slack_bias: float = 0.8):
    return RollingUrgencyConstructor(lookahead=lookahead, slack_bias=slack_bias)
