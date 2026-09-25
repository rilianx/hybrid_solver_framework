from __future__ import annotations

from functools import lru_cache
from typing import Tuple

import pulp

from examples.lotsizing.instance import CLSPInstance


def canonical(sol):
    return tuple(tuple(bool(v) for v in row) for row in sol)


def from_answer(inst, answer):
    return canonical(answer)


def trivial_solution(inst):
    return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def random_solution(inst, rng):
    return tuple(tuple(bool(rng.getrandbits(1)) for _ in range(inst.n_periods)) for _ in range(inst.n_items))


@lru_cache(maxsize=None)
def _solve_plan(inst: CLSPInstance, sol: Tuple[Tuple[bool, ...], ...]):
    n_items, n_periods = inst.n_items, inst.n_periods
    y = sol

    def build_problem(stage: int, unmet_limit: float | None = None):
        prob = pulp.LpProblem("CLSP_heuristic_view", pulp.LpMinimize)
        x = pulp.LpVariable.dicts(
            "x",
            ((i, t) for i in range(n_items) for t in range(n_periods)),
            lowBound=0,
            cat="Continuous",
        )
        inv = pulp.LpVariable.dicts(
            "inv",
            ((i, t) for i in range(n_items) for t in range(n_periods)),
            lowBound=0,
            cat="Continuous",
        )
        short = pulp.LpVariable.dicts(
            "short",
            ((i, t) for i in range(n_items) for t in range(n_periods)),
            lowBound=0,
            cat="Continuous",
        )

        # Inventory balance with shortages
        for i in range(n_items):
            for t in range(n_periods):
                lhs = x[(i, t)] + short[(i, t)]
                if t == 0:
                    prob += lhs == inst.demand[i][t] + inv[(i, t)]
                else:
                    prob += inv[(i, t - 1)] + lhs == inst.demand[i][t] + inv[(i, t)]

        # Capacity and setup-link
        for t in range(n_periods):
            prob += (
                pulp.lpSum(x[(i, t)] for i in range(n_items))
                + pulp.lpSum(inst.setup_time[i] * float(y[i][t]) for i in range(n_items))
                <= inst.capacity[t]
            )
            for i in range(n_items):
                prob += x[(i, t)] <= inst.capacity[t] * float(y[i][t])

        if stage == 1:
            prob += pulp.lpSum(short[(i, t)] for i in range(n_items) for t in range(n_periods))
        else:
            if unmet_limit is not None:
                prob += pulp.lpSum(short[(i, t)] for i in range(n_items) for t in range(n_periods)) == unmet_limit
            prob += pulp.lpSum(inst.holding_cost[i] * inv[(i, t)] for i in range(n_items) for t in range(n_periods))

        return prob, x, inv, short

    # Stage 1: minimize unmet demand
    prob1, x1, inv1, short1 = build_problem(stage=1)
    prob1.solve(pulp.PULP_CBC_CMD(msg=False))
    unmet = pulp.value(pulp.lpSum(short1[(i, t)] for i in range(n_items) for t in range(n_periods)))
    if unmet is None:
        unmet = float("inf")

    # Stage 2: minimize inventory given minimum unmet demand
    prob2, x2, inv2, short2 = build_problem(stage=2, unmet_limit=unmet)
    prob2.solve(pulp.PULP_CBC_CMD(msg=False))
    inv_cost = pulp.value(
        pulp.lpSum(inst.holding_cost[i] * inv2[(i, t)] for i in range(n_items) for t in range(n_periods))
    )
    if inv_cost is None:
        inv_cost = float("inf")

    setup_cost = sum(
        inst.setup_cost[i] * sum(1 for t in range(n_periods) if y[i][t]) for i in range(n_items)
    )

    return float(unmet), float(setup_cost), float(inv_cost)


def violations(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    unmet, _, _ = _solve_plan(inst, sol)
    return {"demanda": unmet}


def cost_terms(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    unmet, setup, inventory = _solve_plan(inst, sol)
    return {"setup": setup, "inventario": inventory}
