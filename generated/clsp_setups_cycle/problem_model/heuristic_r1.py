from __future__ import annotations

from functools import lru_cache
from random import Random
from typing import Iterable

import pulp

from examples.lotsizing.instance import CLSPInstance


def canonical(sol):
    return tuple(tuple(bool(v) for v in row) for row in sol)


def trivial_solution(inst):
    return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def random_solution(inst, rng):
    return tuple(tuple(bool(rng.getrandbits(1)) for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def from_answer(inst, answer):
    return canonical(answer)


@lru_cache(maxsize=None)
def _solve_optimal_production(inst: CLSPInstance, sol):
    n_items = inst.n_items
    n_periods = inst.n_periods
    demand = inst.demand
    setup = sol

    def build_model(minimize_inventory: bool, target_unmet: float | None = None):
        prob = pulp.LpProblem("clsp_production", pulp.LpMinimize)
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
            (i, t): pulp.LpVariable(f"unmet_{i}_{t}", lowBound=0, upBound=demand[i][t])
            for i in range(n_items)
            for t in range(n_periods)
        }

        for t in range(n_periods):
            prob += (
                pulp.lpSum(x[i, t] for i in range(n_items))
                + pulp.lpSum(inst.setup_time[i] * (1.0 if setup[i][t] else 0.0) for i in range(n_items))
                <= inst.capacity[t]
            )
            for i in range(n_items):
                if not setup[i][t]:
                    prob += x[i, t] == 0

        for i in range(n_items):
            for t in range(n_periods):
                prev_inv = inv[i, t - 1] if t > 0 else 0
                prob += prev_inv + x[i, t] + unmet[i, t] == demand[i][t] + inv[i, t]

        if target_unmet is not None:
            prob += pulp.lpSum(unmet[i, t] for i in range(n_items) for t in range(n_periods)) == target_unmet
            prob += pulp.lpSum(inst.holding_cost[i] * inv[i, t] for i in range(n_items) for t in range(n_periods))
        else:
            prob += pulp.lpSum(unmet[i, t] for i in range(n_items) for t in range(n_periods))

        return prob, x, inv, unmet

    prob1, x1, inv1, unmet1 = build_model(minimize_inventory=False)
    prob1.solve(pulp.PULP_CBC_CMD(msg=False))
    status1 = pulp.LpStatus[prob1.status]
    if status1 not in {"Optimal", "Integer Feasible"}:
        # Should not happen for valid instances; fall back to maximal coverage 0 if needed.
        min_unmet = sum(sum(row) for row in demand)
    else:
        min_unmet = float(pulp.value(pulp.lpSum(unmet1[i, t] for i in range(n_items) for t in range(n_periods))))

    prob2, x2, inv2, unmet2 = build_model(minimize_inventory=True, target_unmet=min_unmet)
    prob2.solve(pulp.PULP_CBC_CMD(msg=False))

    total_unmet = float(
        sum(pulp.value(unmet2[i, t]) for i in range(n_items) for t in range(n_periods))
    )
    total_inventory = float(
        sum(inst.holding_cost[i] * pulp.value(inv2[i, t]) for i in range(n_items) for t in range(n_periods))
    )
    return {
        "unmet": max(0.0, total_unmet),
        "inventory": max(0.0, total_inventory),
    }


def violations(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    res = _solve_optimal_production(inst, sol)
    unmet = res["unmet"]
    return {"demanda": 0.0 if unmet <= 1e-9 else unmet}


def cost_terms(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    setup_cost = sum(
        inst.setup_cost[i]
        for i in range(inst.n_items)
        for t in range(inst.n_periods)
        if sol[i][t]
    )
    res = _solve_optimal_production(inst, sol)
    return {"setup": float(setup_cost), "inventario": float(res["inventory"])}
