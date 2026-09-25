from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "forward_urgency_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "slack_bias": {"type": "float", "range": [0.0, 2.0]},
        "max_repairs": {"type": "int", "range": [1, 50]},
    },
}


class ForwardUrgencyConstructor:
    """Construcción codiciosa hacia adelante: abre setups cuando la carga acumulada amenaza la capacidad futura."""

    def __init__(self, problem: LotSizingModel, slack_bias: float = 0.75, max_repairs: int = 12):
        self.problem = problem
        self.slack_bias = slack_bias
        self.max_repairs = max_repairs

    def _empty_sol(self, inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol: Tuple[Tuple[bool, ...], ...], i: int, t: int, value: bool) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(
            tuple(value if (ii == i and tt == t) else sol[ii][tt] for tt in range(len(sol[0])))
            for ii in range(len(sol))
        )

    def _count_period_load(self, sol, inst):
        return [
            sum(inst.setup_time[i] for i in range(inst.n_items) if sol[i][t])
            for t in range(inst.n_periods)
        ]

    def _greedy_build(self, inst: CLSPInstance, rng: Random):
        n, T = inst.n_items, inst.n_periods
        sol = self._empty_sol(inst)

        demand_prefix = [0.0] * T
        for t in range(T):
            demand_prefix[t] = sum(inst.demand[i][t] for i in range(n)) + (demand_prefix[t - 1] if t else 0.0)

        # Items with larger setup time and more lumpy demand get earlier protection.
        item_order = list(range(n))
        item_order.sort(
            key=lambda i: (
                -inst.setup_time[i],
                -sum(1 for d in inst.demand[i] if d > 0),
                -inst.setup_cost[i],
                rng.random(),
            )
        )

        # Base plan: setup on every positive-demand period, then add earlier setups
        # if the forward capacity balance looks tight.
        for i in item_order:
            last_setup = None
            for t in range(T):
                if inst.demand[i][t] > 0:
                    if last_setup is None or t > last_setup + 1:
                        sol = self._set(sol, i, t, True)
                        last_setup = t

            # If all demand is concentrated, add an early setup to hedge inventory.
            positive = [t for t in range(T) if inst.demand[i][t] > 0]
            if positive and positive[0] > 0 and rng.random() < 0.5:
                sol = self._set(sol, i, positive[0] - 1, True)

        # Forward repair: if a prefix looks too tight, add an extra setup earlier for
        # a high-demand item that has slack in previous periods.
        for _ in range(self.max_repairs):
            if self.problem.is_feasible(sol):
                return sol
            load = self._count_period_load(sol, inst)
            worst_t = max(range(T), key=lambda t: load[t] / max(inst.capacity[t], 1e-9))
            if load[worst_t] <= inst.capacity[worst_t]:
                break

            candidates = []
            for i in range(n):
                if not sol[i][worst_t]:
                    continue
                for tt in range(worst_t):
                    if not sol[i][tt]:
                        score = (
                            inst.capacity[tt] - load[tt],
                            -inst.holding_cost[i],
                            -sum(inst.demand[i][worst_t:]),
                            rng.random(),
                        )
                        candidates.append((score, i, tt))
            if not candidates:
                break
            candidates.sort(reverse=True)
            _, i, tt = candidates[0]
            sol = self._set(sol, i, tt, True)

        return sol

    def build(self, inst: CLSPInstance, rng: Random):
        sol = self._greedy_build(inst, rng)
        if self.problem.is_feasible(sol):
            return sol

        # Final conservative fallback: progressively densify selected items in early periods.
        n, T = inst.n_items, inst.n_periods
        items = sorted(range(n), key=lambda i: (-sum(inst.demand[i]), -inst.setup_time[i], rng.random()))
        periods = sorted(range(T), key=lambda t: (inst.capacity[t], t))
        for i in items:
            for t in periods:
                if not sol[i][t]:
                    sol = self._set(sol, i, t, True)
                    if self.problem.is_feasible(sol):
                        return sol

        return sol


def build_component(problem, slack_bias: float = 0.75, max_repairs: int = 12):
    return ForwardUrgencyConstructor(problem, slack_bias=slack_bias, max_repairs=max_repairs)
