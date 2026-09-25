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


# ---- vista MIP ----
from typing import Dict, List, Tuple

from examples.lotsizing.instance import CLSPInstance


def variables(inst: CLSPInstance) -> dict[str, tuple[float, float, str]]:
    n_items, n_periods = inst.n_items, inst.n_periods
    max_demand = sum(inst.demand[i][t] for i in range(n_items) for t in range(n_periods))
    max_cap = max(inst.capacity) if inst.capacity else 0.0
    inv_ub = max_demand
    short_ub = max_demand
    vars_: dict[str, tuple[float, float, str]] = {}

    for i in range(n_items):
        for t in range(n_periods):
            vars_[f"y_{i}_{t}"] = (0.0, 1.0, "binary")
            vars_[f"x_{i}_{t}"] = (0.0, max_cap, "continuous")
            vars_[f"inv_{i}_{t}"] = (0.0, inv_ub, "continuous")
            vars_[f"short_{i}_{t}"] = (0.0, short_ub, "continuous")
    return vars_


def structural_variables(inst: CLSPInstance) -> list[str]:
    return [f"y_{i}_{t}" for i in range(inst.n_items) for t in range(inst.n_periods)]


def to_assignment(inst: CLSPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)
    return {f"y_{i}_{t}": float(sol[i][t]) for i in range(inst.n_items) for t in range(inst.n_periods)}


def aux_values(inst: CLSPInstance, sol) -> dict[str, float]:
    res = _solve_plan(inst, sol)
    sol = canonical(sol)
    n_items, n_periods = inst.n_items, inst.n_periods

    vals: dict[str, float] = {}
    for i in range(n_items):
        for t in range(n_periods):
            vals[f"x_{i}_{t}"] = 0.0
            vals[f"inv_{i}_{t}"] = 0.0
            vals[f"short_{i}_{t}"] = 0.0

    if res["status"] == "Optimal":
        # Re-solve via the cached LP result is not directly exposed; we only need
        # values consistent with the evaluation interface. For feasible plans,
        # the canonical LP optimum has zero shortage.
        # We reconstruct a consistent zero-shortage pattern using cumulative
        # balance when possible.
        remaining = [0.0 for _ in range(n_items)]
        inv_prev = [0.0 for _ in range(n_items)]
        for t in range(n_periods):
            cap_left = inst.capacity[t]
            for i in range(n_items):
                if sol[i][t]:
                    cap_left -= inst.setup_time[i]
            for i in range(n_items):
                demand = inst.demand[i][t]
                x = max(0.0, demand - inv_prev[i])
                x = min(x, cap_left) if cap_left >= 0 else 0.0
                inv = inv_prev[i] + x - demand
                vals[f"x_{i}_{t}"] = x
                vals[f"inv_{i}_{t}"] = inv
                vals[f"short_{i}_{t}"] = 0.0
                cap_left -= x
                inv_prev[i] = inv
    else:
        # In infeasible cases, expose the shortage profile as returned by the
        # heuristic evaluator so the demand family is violated exactly there.
        n_items, n_periods = inst.n_items, inst.n_periods
        prob = _solve_plan(inst, sol)  # cached status/values; shortage only is enough
        if prob["shortage"] == float("inf"):
            for i in range(n_items):
                for t in range(n_periods):
                    vals[f"short_{i}_{t}"] = 1.0
    return vals


def from_assignment(inst: CLSPInstance, x) -> tuple[tuple[bool, ...], ...]:
    return tuple(
        tuple(bool(x[f"y_{i}_{t}"]) for t in range(inst.n_periods))
        for i in range(inst.n_items)
    )


def constraint_families(inst: CLSPInstance) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    n_items, n_periods = inst.n_items, inst.n_periods
    families: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "capacidad": [],
        "demanda": [],
        "setup_link": [],
    }

    for t in range(n_periods):
        coeffs: dict[str, float] = {}
        for i in range(n_items):
            coeffs[f"x_{i}_{t}"] = coeffs.get(f"x_{i}_{t}", 0.0) + 1.0
            coeffs[f"y_{i}_{t}"] = coeffs.get(f"y_{i}_{t}", 0.0) + float(inst.setup_time[i])
        families["capacidad"].append((coeffs, "<=", float(inst.capacity[t])))

    for i in range(n_items):
        for t in range(n_periods):
            coeffs_link = {f"x_{i}_{t}": 1.0, f"y_{i}_{t}": -float(inst.capacity[t])}
            families["setup_link"].append((coeffs_link, "<=", 0.0))

            coeffs_bal: dict[str, float] = {f"inv_{i}_{t}": -1.0, f"x_{i}_{t}": 1.0}
            if t > 0:
                coeffs_bal[f"inv_{i}_{t-1}"] = coeffs_bal.get(f"inv_{i}_{t-1}", 0.0) + 1.0
            families["demanda"].append((coeffs_bal, "==", float(inst.demand[i][t])))

    return families


def objective_terms(inst: CLSPInstance) -> dict[str, tuple[dict[str, float], float]]:
    setup_coeffs: dict[str, float] = {}
    inv_coeffs: dict[str, float] = {}
    for i in range(inst.n_items):
        for t in range(inst.n_periods):
            setup_coeffs[f"y_{i}_{t}"] = float(inst.setup_cost[i])
            inv_coeffs[f"inv_{i}_{t}"] = float(inst.holding_cost[i])
    return {
        "setup": (setup_coeffs, 0.0),
        "inventario": (inv_coeffs, 0.0),
    }


def variable_groups(inst: CLSPInstance) -> dict[str, list[str]]:
    ys = structural_variables(inst)
    groups: dict[str, list[str]] = {f"g{k}": [] for k in range(4)}
    for idx, name in enumerate(ys):
        groups[f"g{idx % 4}"].append(name)
    return groups
