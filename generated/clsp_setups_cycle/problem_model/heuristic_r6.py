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
    exact = _solve_fixed_plan(inst, sol, allow_unmet=False)
    if exact is not None:
        return 0.0, exact[1]
    relaxed = _solve_fixed_plan(inst, sol, allow_unmet=True)
    if relaxed is None:
        return float("inf"), float("inf")
    return relaxed


def violations(inst, sol) -> dict[str, float]:
    unmet, _ = _optimal_plan_stats(inst, sol)
    return {"demanda": float(unmet)}


def cost_terms(inst, sol) -> dict[str, float]:
    y = canonical(sol)
    setup_cost = sum(
        inst.setup_cost[i] * sum(1 for t in range(inst.n_periods) if y[i][t])
        for i in range(inst.n_items)
    )
    unmet, inv_cost = _optimal_plan_stats(inst, y)
    return {
        "setup": float(setup_cost),
        "inventario": float(inv_cost),
        "demanda": float(unmet),
        "total": float(setup_cost + inv_cost + unmet),
    }


def _solve_fixed_plan(inst, sol, allow_unmet: bool):
    y = canonical(sol)
    n_items, n_periods = inst.n_items, inst.n_periods
    item_total_demand = [sum(inst.demand[i]) for i in range(n_items)]

    def build_problem(minimize_unmet: bool, unmet_cap: float | None = None):
        prob = pulp.LpProblem("CLSP_fixed_plan", pulp.LpMinimize)

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
        unmet = None
        if allow_unmet:
            unmet = {
                (i, t): pulp.LpVariable(f"unmet_{i}_{t}", lowBound=0, upBound=inst.demand[i][t])
                for i in range(n_items)
                for t in range(n_periods)
            }

        for t in range(n_periods):
            prob += (
                pulp.lpSum(x[(i, t)] for i in range(n_items))
                + pulp.lpSum(inst.setup_time[i] * (1 if y[i][t] else 0) for i in range(n_items))
                <= inst.capacity[t]
            ), f"capacity_{t}"

        for i in range(n_items):
            for t in range(n_periods):
                prob += x[(i, t)] <= item_total_demand[i] * (1 if y[i][t] else 0), f"setup_link_{i}_{t}"
                prev_inv = 0 if t == 0 else inv[(i, t - 1)]
                if allow_unmet:
                    prob += (
                        prev_inv + x[(i, t)] + unmet[(i, t)] == inst.demand[i][t] + inv[(i, t)]
                    ), f"balance_{i}_{t}"
                else:
                    prob += prev_inv + x[(i, t)] == inst.demand[i][t] + inv[(i, t)], f"balance_{i}_{t}"

        if allow_unmet:
            total_unmet = pulp.lpSum(unmet.values())
            if minimize_unmet:
                prob += total_unmet, "min_unmet"
            else:
                prob += pulp.lpSum(inst.holding_cost[i] * inv[(i, t)] for i in range(n_items) for t in range(n_periods)), "min_inv"
                if unmet_cap is not None:
                    prob += total_unmet == unmet_cap, "fix_unmet"
        else:
            prob += pulp.lpSum(inst.holding_cost[i] * inv[(i, t)] for i in range(n_items) for t in range(n_periods)), "min_inv"

        return prob, x, inv, unmet

    if allow_unmet:
        prob, x, inv, unmet = build_problem(minimize_unmet=True)
        status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[status] != "Optimal":
            return None
        unmet_opt = float(sum(pulp.value(unmet[(i, t)]) for i in range(n_items) for t in range(n_periods)))
        prob, x, inv, unmet = build_problem(minimize_unmet=False, unmet_cap=unmet_opt)
        status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[status] != "Optimal":
            return None
        inv_val = sum(pulp.value(inv[(i, t)]) for i in range(n_items) for t in range(n_periods))
        return float(unmet_opt), float(inv_val)

    prob, x, inv, unmet = build_problem(minimize_unmet=False)
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        return None
    inv_val = sum(pulp.value(inv[(i, t)]) for i in range(n_items) for t in range(n_periods))
    return 0.0, float(inv_val)
