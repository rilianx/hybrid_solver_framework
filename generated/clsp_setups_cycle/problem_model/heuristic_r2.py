from __future__ import annotations

from functools import lru_cache
from random import Random
from typing import Iterable

import pulp

from examples.lotsizing.instance import CLSPInstance


def canonical(sol):
    return tuple(tuple(bool(v) for v in row) for row in sol)


def trivial_solution(inst):
    n_items, n_periods = inst.n_items, inst.n_periods
    prob = pulp.LpProblem("CLSP_trivial_solution", pulp.LpMinimize)

    y = {
        (i, t): pulp.LpVariable(f"y_{i}_{t}", lowBound=0, upBound=1, cat="Binary")
        for i in range(n_items)
        for t in range(n_periods)
    }
    x = {
        (i, t): pulp.LpVariable(f"x_{i}_{t}", lowBound=0)
        for i in range(n_items)
        for t in range(n_periods)
    }
    inv = {
        (i, t): pulp.LpVariable(f"inv_{i}_{t}", lowBound=0)
        for i in range(n_items)
        for t in range(n_periods)
    }

    for t in range(n_periods):
        prob += (
            pulp.lpSum(x[(i, t)] for i in range(n_items))
            + pulp.lpSum(inst.setup_time[i] * y[(i, t)] for i in range(n_items))
            <= inst.capacity[t]
        ), f"capacity_{t}"

    for i in range(n_items):
        for t in range(n_periods):
            prob += x[(i, t)] <= sum(inst.demand[i]) * y[(i, t)], f"setup_link_{i}_{t}"
            prev_inv = 0 if t == 0 else inv[(i, t - 1)]
            prob += prev_inv + x[(i, t)] == inst.demand[i][t] + inv[(i, t)], f"balance_{i}_{t}"

    prob += pulp.lpSum(inst.setup_cost[i] * y[(i, t)] for i in range(n_items) for t in range(n_periods)) + pulp.lpSum(
        inst.holding_cost[i] * inv[(i, t)] for i in range(n_items) for t in range(n_periods)
    )

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        return tuple(tuple(True for _ in range(n_periods)) for _ in range(n_items))
    return tuple(
        tuple(bool(pulp.value(y[(i, t)]) > 0.5) for t in range(n_periods))
        for i in range(n_items)
    )


def random_solution(inst, rng):
    return tuple(tuple(bool(rng.getrandbits(1)) for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def from_answer(inst, answer):
    return canonical(answer)


@lru_cache(maxsize=None)
def _optimal_plan_stats(inst, sol):
    y = canonical(sol)
    n_items, n_periods = inst.n_items, inst.n_periods
    item_total_demand = [sum(inst.demand[i]) for i in range(n_items)]

    def solve(stage2_target_unmet=None):
        prob = pulp.LpProblem("CLSP_plan_evaluation", pulp.LpMinimize)

        x = {
            (i, t): pulp.LpVariable(f"x_{i}_{t}", lowBound=0)
            for i in range(n_items)
            for t in range(n_periods)
        }
        inv = {
            (i, t): pulp.LpVariable(f"inv_{i}_{t}", lowBound=0)
            for i in range(n_items)
            for t in range(n_periods)
        }
        unmet = {
            (i, t): pulp.LpVariable(f"unmet_{i}_{t}", lowBound=0, upBound=inst.demand[i][t])
            for i in range(n_items)
            for t in range(n_periods)
        }

        for t in range(n_periods):
            cap_expr = pulp.lpSum(x[(ii, t)] for ii in range(n_items)) + pulp.lpSum(
                inst.setup_time[ii] * (1 if y[ii][t] else 0) for ii in range(n_items)
            )
            prob += cap_expr <= inst.capacity[t], f"capacity_{t}"

        for i in range(n_items):
            for t in range(n_periods):
                prob += x[(i, t)] <= item_total_demand[i] * (1 if y[i][t] else 0), f"setup_link_{i}_{t}"
                prev_inv = 0 if t == 0 else inv[(i, t - 1)]
                prob += prev_inv + x[(i, t)] + unmet[(i, t)] == inst.demand[i][t] + inv[(i, t)], f"balance_{i}_{t}"

        if stage2_target_unmet is None:
            prob += pulp.lpSum(unmet.values())
        else:
            prob += pulp.lpSum(inst.holding_cost[i] * inv[(i, t)] for i in range(n_items) for t in range(n_periods))
            prob += pulp.lpSum(unmet.values()) == stage2_target_unmet, "fix_unmet"

        status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[status] != "Optimal":
            return None

        unmet_val = sum(pulp.value(unmet[(i, t)]) for i in range(n_items) for t in range(n_periods))
        inv_val = sum(pulp.value(inv[(i, t)]) for i in range(n_items) for t in range(n_periods))
        return unmet_val, inv_val

    first = solve()
    if first is None:
        return float("inf"), float("inf")

    best_unmet, _ = first
    second = solve(stage2_target_unmet=best_unmet)
    if second is None:
        return best_unmet, float("inf")
    return second


def violations(inst, sol) -> dict[str, float]:
    y = canonical(sol)
    unmet, _ = _optimal_plan_stats(inst, y)
    return {"demanda": float(unmet)}


def cost_terms(inst, sol) -> dict[str, float]:
    y = canonical(sol)
    setup_cost = sum(
        inst.setup_cost[i] * sum(1 for t in range(inst.n_periods) if y[i][t])
        for i in range(inst.n_items)
    )
    _, inv_cost = _optimal_plan_stats(inst, y)
    return {"setup": float(setup_cost), "inventario": float(inv_cost)}
