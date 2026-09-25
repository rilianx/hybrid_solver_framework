from __future__ import annotations

from functools import lru_cache
from typing import Iterable
import random

import pulp

from examples.lotsizing.instance import CLSPInstance


def canonical(sol):
    return tuple(tuple(bool(v) for v in row) for row in sol)


def trivial_solution(inst):
    return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def random_solution(inst, rng):
    return tuple(
        tuple(bool(rng.getrandbits(1)) for _ in range(inst.n_periods))
        for _ in range(inst.n_items)
    )


def from_answer(inst, answer):
    return canonical(answer)


def _as_key(inst: CLSPInstance, sol):
    return inst, canonical(sol)


@lru_cache(maxsize=None)
def _solve_plan(inst: CLSPInstance, sol):
    sol = canonical(sol)
    n_items = inst.n_items
    n_periods = inst.n_periods

    prob = pulp.LpProblem("clsp_plan_eval", pulp.LpMinimize)

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
    short = {
        (i, t): pulp.LpVariable(f"short_{i}_{t}", lowBound=0)
        for i in range(n_items)
        for t in range(n_periods)
    }

    total_demand = sum(inst.demand[i][t] for i in range(n_items) for t in range(n_periods))
    total_h = sum(inst.holding_cost)
    big_m = 1.0 + total_h * max(1.0, total_demand)

    prob += (
        big_m * pulp.lpSum(short[i, t] for i in range(n_items) for t in range(n_periods))
        + pulp.lpSum(inst.holding_cost[i] * inv[i, t] for i in range(n_items) for t in range(n_periods))
    )

    for t in range(n_periods):
        prob += (
            pulp.lpSum(x[i, t] for i in range(n_items))
            + pulp.lpSum(inst.setup_time[i] * float(sol[i][t]) for i in range(n_items))
            <= inst.capacity[t]
        )

    for i in range(n_items):
        for t in range(n_periods):
            if not sol[i][t]:
                prob += x[i, t] == 0
            else:
                prob += x[i, t] <= inst.capacity[t]

            prev_inv = inv[i, t - 1] if t > 0 else 0
            prob += prev_inv + x[i, t] + short[i, t] == inst.demand[i][t] + inv[i, t]

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        return {
            "status": status,
            "shortage": float("inf"),
            "inventory": float("inf"),
        }

    shortage = sum(pulp.value(short[i, t]) for i in range(n_items) for t in range(n_periods))
    inventory = sum(
        inst.holding_cost[i] * pulp.value(inv[i, t])
        for i in range(n_items)
        for t in range(n_periods)
    )
    return {
        "status": status,
        "shortage": float(shortage),
        "inventory": float(inventory),
    }


def violations(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    res = _solve_plan(inst, sol)
    return {"demanda": float(res["shortage"])}


def cost_terms(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    setup = sum(
        inst.setup_cost[i]
        for i in range(inst.n_items)
        for t in range(inst.n_periods)
        if sol[i][t]
    )
    res = _solve_plan(inst, sol)
    return {
        "setup": float(setup),
        "inventario": float(res["inventory"]),
    }
