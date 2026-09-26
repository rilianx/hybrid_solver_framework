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
from functools import lru_cache

from examples.lotsizing.instance import CLSPInstance
import pulp


def _plan_eval_lp(inst: CLSPInstance, sol):
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
            "x": {(i, t): 0.0 for i in range(n_items) for t in range(n_periods)},
            "inv": {(i, t): 0.0 for i in range(n_items) for t in range(n_periods)},
            "short": {(i, t): 0.0 for i in range(n_items) for t in range(n_periods)},
            "shortage": float("inf"),
            "inventory": float("inf"),
        }

    xval = {(i, t): float(pulp.value(x[i, t])) for i in range(n_items) for t in range(n_periods)}
    invval = {(i, t): float(pulp.value(inv[i, t])) for i in range(n_items) for t in range(n_periods)}
    shortval = {(i, t): float(pulp.value(short[i, t])) for i in range(n_items) for t in range(n_periods)}
    shortage = sum(shortval.values())
    inventory = sum(inst.holding_cost[i] * invval[i, t] for i in range(n_items) for t in range(n_periods))
    return {
        "status": status,
        "x": xval,
        "inv": invval,
        "short": shortval,
        "shortage": float(shortage),
        "inventory": float(inventory),
    }


@lru_cache(maxsize=None)
def _cached_plan_eval(inst: CLSPInstance, sol):
    return _plan_eval_lp(inst, sol)


def variables(inst) -> dict[str, tuple[float, float, str]]:
    n_items, n_periods = inst.n_items, inst.n_periods
    max_demand = sum(inst.demand[i][t] for i in range(n_items) for t in range(n_periods))
    max_cap = max(inst.capacity) if inst.capacity else 0.0
    out: dict[str, tuple[float, float, str]] = {}

    for i in range(n_items):
        for t in range(n_periods):
            out[f"y_{i}_{t}"] = (0.0, 1.0, "binary")
            out[f"x_{i}_{t}"] = (0.0, max_cap, "continuous")
            out[f"inv_{i}_{t}"] = (0.0, max_demand, "continuous")
            out[f"short_{i}_{t}"] = (0.0, max_demand, "continuous")
    return out


def structural_variables(inst) -> list[str]:
    return [f"y_{i}_{t}" for i in range(inst.n_items) for t in range(inst.n_periods)]


def to_assignment(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    return {f"y_{i}_{t}": float(sol[i][t]) for i in range(inst.n_items) for t in range(inst.n_periods)}


def aux_values(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    data = _cached_plan_eval(inst, sol)
    vals: dict[str, float] = {}
    for i in range(inst.n_items):
        for t in range(inst.n_periods):
            vals[f"x_{i}_{t}"] = data["x"][i, t]
            vals[f"inv_{i}_{t}"] = data["inv"][i, t]
            vals[f"short_{i}_{t}"] = data["short"][i, t]
    return vals


def from_assignment(inst, x) -> tuple[tuple[bool, ...], ...]:
    return tuple(
        tuple(bool(x[f"y_{i}_{t}"]) for t in range(inst.n_periods))
        for i in range(inst.n_items)
    )


def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    n_items, n_periods = inst.n_items, inst.n_periods
    families: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "capacidad": [],
        "demanda": [],
        "enlace": [],
    }

    for t in range(n_periods):
        coeffs: dict[str, float] = {}
        for i in range(n_items):
            coeffs[f"x_{i}_{t}"] = coeffs.get(f"x_{i}_{t}", 0.0) + 1.0
            coeffs[f"y_{i}_{t}"] = coeffs.get(f"y_{i}_{t}", 0.0) + float(inst.setup_time[i])
        families["capacidad"].append((coeffs, "<=", float(inst.capacity[t])))

    for i in range(n_items):
        for t in range(n_periods):
            coeffs = {f"inv_{i}_{t}": 1.0, f"x_{i}_{t}": -1.0, f"short_{i}_{t}": -1.0}
            if t > 0:
                coeffs[f"inv_{i}_{t-1}"] = coeffs.get(f"inv_{i}_{t-1}", 0.0) - 1.0
            families["demanda"].append((coeffs, "==", -float(inst.demand[i][t])))

            coeffs2 = {f"x_{i}_{t}": 1.0, f"y_{i}_{t}": -float(inst.capacity[t])}
            families["enlace"].append((coeffs2, "<=", 0.0))

    return families


def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]:
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


def variable_groups(inst) -> dict[str, list[str]]:
    ys = structural_variables(inst)
    groups: dict[str, list[str]] = {f"g{k}": [] for k in range(4)}
    for idx, name in enumerate(ys):
        groups[f"g{idx % 4}"].append(name)
    return groups
