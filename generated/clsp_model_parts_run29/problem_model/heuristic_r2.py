from __future__ import annotations

from functools import lru_cache
from random import Random

import pulp

from examples.lotsizing.instance import CLSPInstance


def _setup_time(inst, i: int) -> float:
    if hasattr(inst, "setup_time"):
        return float(inst.setup_time[i])
    if hasattr(inst, "setup_times"):
        return float(inst.setup_times[i])
    if hasattr(inst, "st"):
        return float(inst.st[i])
    raise AttributeError("Instance has no setup-time attribute")


def _setup_cost(inst, i: int) -> float:
    if hasattr(inst, "setup_cost"):
        return float(inst.setup_cost[i])
    if hasattr(inst, "setup_costs"):
        return float(inst.setup_costs[i])
    if hasattr(inst, "s"):
        return float(inst.s[i])
    raise AttributeError("Instance has no setup-cost attribute")


def _holding_cost(inst, i: int) -> float:
    if hasattr(inst, "holding_cost"):
        return float(inst.holding_cost[i])
    if hasattr(inst, "holding_costs"):
        return float(inst.holding_costs[i])
    if hasattr(inst, "h"):
        return float(inst.h[i])
    raise AttributeError("Instance has no holding-cost attribute")


def canonical(sol):
    return tuple(tuple(bool(v) for v in row) for row in sol)


def from_answer(inst, answer):
    return canonical(answer)


def trivial_solution(inst):
    return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def random_solution(inst, rng: Random):
    return tuple(
        tuple(bool(rng.getrandbits(1)) for _ in range(inst.n_periods))
        for _ in range(inst.n_items)
    )


def _build_and_solve(inst: CLSPInstance, sol):
    n_items, n_periods = inst.n_items, inst.n_periods
    y = canonical(sol)

    # Stage 1: minimize total unmet demand.
    prob1 = pulp.LpProblem("clsp_stage1", pulp.LpMinimize)
    x = pulp.LpVariable.dicts("x", (range(n_items), range(n_periods)), lowBound=0)
    inv = pulp.LpVariable.dicts("inv", (range(n_items), range(n_periods)), lowBound=0)
    short = pulp.LpVariable.dicts("short", (range(n_items), range(n_periods)), lowBound=0)

    for i in range(n_items):
        for t in range(n_periods):
            prev_inv = 0 if t == 0 else inv[i][t - 1]
            prob1 += prev_inv + x[i][t] + short[i][t] == inst.demand[i][t] + inv[i][t]
            prob1 += x[i][t] <= inst.capacity[t] * (1.0 if y[i][t] else 0.0)

    for t in range(n_periods):
        prob1 += (
            pulp.lpSum(x[i][t] for i in range(n_items))
            + pulp.lpSum(_setup_time(inst, i) * (1.0 if y[i][t] else 0.0) for i in range(n_items))
            <= inst.capacity[t]
        )

    prob1 += pulp.lpSum(short[i][t] for i in range(n_items) for t in range(n_periods))
    prob1.solve(pulp.PULP_CBC_CMD(msg=False))
    min_short = float(pulp.value(prob1.objective) or 0.0)

    # Stage 2: among minimum-shortage solutions, minimize inventory cost.
    prob2 = pulp.LpProblem("clsp_stage2", pulp.LpMinimize)
    x2 = pulp.LpVariable.dicts("x", (range(n_items), range(n_periods)), lowBound=0)
    inv2 = pulp.LpVariable.dicts("inv", (range(n_items), range(n_periods)), lowBound=0)
    short2 = pulp.LpVariable.dicts("short", (range(n_items), range(n_periods)), lowBound=0)

    for i in range(n_items):
        for t in range(n_periods):
            prev_inv = 0 if t == 0 else inv2[i][t - 1]
            prob2 += prev_inv + x2[i][t] + short2[i][t] == inst.demand[i][t] + inv2[i][t]
            prob2 += x2[i][t] <= inst.capacity[t] * (1.0 if y[i][t] else 0.0)

    for t in range(n_periods):
        prob2 += (
            pulp.lpSum(x2[i][t] for i in range(n_items))
            + pulp.lpSum(_setup_time(inst, i) * (1.0 if y[i][t] else 0.0) for i in range(n_items))
            <= inst.capacity[t]
        )

    prob2 += pulp.lpSum(short2[i][t] for i in range(n_items) for t in range(n_periods)) == min_short
    prob2 += pulp.lpSum(_holding_cost(inst, i) * inv2[i][t] for i in range(n_items) for t in range(n_periods))
    prob2.solve(pulp.PULP_CBC_CMD(msg=False))

    inventory = float(
        pulp.value(pulp.lpSum(_holding_cost(inst, i) * inv2[i][t] for i in range(n_items) for t in range(n_periods)))
        or 0.0
    )
    shortage = float(pulp.value(pulp.lpSum(short2[i][t] for i in range(n_items) for t in range(n_periods))) or 0.0)

    return {"shortage": shortage, "inventory": inventory}


@lru_cache(maxsize=None)
def _cached_eval(inst: CLSPInstance, sol):
    return _build_and_solve(inst, sol)


def violations(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    evals = _cached_eval(inst, sol)
    return {"demanda": float(evals["shortage"])}


def cost_terms(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    evals = _cached_eval(inst, sol)
    setup = sum(
        _setup_cost(inst, i) * sum(1.0 for t in range(inst.n_periods) if sol[i][t])
        for i in range(inst.n_items)
    )
    return {"setup": float(setup), "inventario": float(evals["inventory"])}
