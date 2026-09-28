from __future__ import annotations

from functools import lru_cache
from random import Random
from typing import Any

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


@lru_cache(maxsize=8192)
def _instance_data(inst_key):
    return inst_key


def _inst_key(inst: CLSPInstance):
    return (
        inst.n_items,
        inst.n_periods,
        tuple(tuple(float(d) for d in row) for row in inst.demand),
        tuple(float(x) for x in inst.capacity),
        tuple(float(x) for x in inst.setup_time),
        tuple(float(x) for x in inst.setup_cost),
        tuple(float(x) for x in inst.holding_cost),
    )


def _key_to_data(inst_key):
    n_items, n_periods, demand, capacity, setup_time, setup_cost, holding_cost = inst_key
    return n_items, n_periods, demand, capacity, setup_time, setup_cost, holding_cost


@lru_cache(maxsize=8192)
def _solve_optimal_production_cached(inst_key, sol):
    n_items, n_periods, demand, capacity, setup_time, setup_cost, holding_cost = _key_to_data(inst_key)
    setup = sol

    def build_model(minimize_inventory: bool, target_unmet: float | None = None):
        prob = pulp.LpProblem("clsp_production", pulp.LpMinimize)
        x = [[pulp.LpVariable(f"x_{i}_{t}", lowBound=0) for t in range(n_periods)] for i in range(n_items)]
        inv = [[pulp.LpVariable(f"inv_{i}_{t}", lowBound=0) for t in range(n_periods)] for i in range(n_items)]
        unmet = [
            [pulp.LpVariable(f"unmet_{i}_{t}", lowBound=0, upBound=demand[i][t]) for t in range(n_periods)]
            for i in range(n_items)
        ]

        for t in range(n_periods):
            prob += (
                pulp.lpSum(x[i][t] for i in range(n_items))
                + pulp.lpSum(setup_time[i] * (1.0 if setup[i][t] else 0.0) for i in range(n_items))
                <= capacity[t]
            )
            for i in range(n_items):
                if not setup[i][t]:
                    prob += x[i][t] == 0

        for i in range(n_items):
            for t in range(n_periods):
                prev_inv = inv[i][t - 1] if t > 0 else 0
                prob += prev_inv + x[i][t] + unmet[i][t] == demand[i][t] + inv[i][t]

        if target_unmet is not None:
            prob += pulp.lpSum(unmet[i][t] for i in range(n_items) for t in range(n_periods)) == target_unmet
            prob += pulp.lpSum(
                holding_cost[i] * inv[i][t] for i in range(n_items) for t in range(n_periods)
            )
        else:
            prob += pulp.lpSum(unmet[i][t] for i in range(n_items) for t in range(n_periods))

        return prob, x, inv, unmet

    prob1, x1, inv1, unmet1 = build_model(minimize_inventory=False)
    prob1.solve(pulp.PULP_CBC_CMD(msg=False))
    status1 = pulp.LpStatus[prob1.status]
    if status1 not in {"Optimal", "Integer Feasible"}:
        min_unmet = sum(sum(row) for row in demand)
    else:
        min_unmet = float(
            pulp.value(pulp.lpSum(unmet1[i][t] for i in range(n_items) for t in range(n_periods)))
        )

    prob2, x2, inv2, unmet2 = build_model(minimize_inventory=True, target_unmet=min_unmet)
    prob2.solve(pulp.PULP_CBC_CMD(msg=False))

    total_unmet = float(sum(pulp.value(unmet2[i][t]) for i in range(n_items) for t in range(n_periods)))
    total_inventory = float(
        sum(holding_cost[i] * pulp.value(inv2[i][t]) for i in range(n_items) for t in range(n_periods))
    )
    return {"unmet": max(0.0, total_unmet), "inventory": max(0.0, total_inventory)}


def _solve_optimal_production(inst: CLSPInstance, sol):
    return _solve_optimal_production_cached(_inst_key(inst), sol)


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


# ---- vista MIP ----
def variables(inst) -> dict[str, tuple[float, float, str]]:
    n_items, n_periods = inst.n_items, inst.n_periods
    big_m = sum(max(0.0, d) for row in inst.demand for d in row)
    vars_: dict[str, tuple[float, float, str]] = {}
    for i in range(n_items):
        for t in range(n_periods):
            vars_[f"y_{i}_{t}"] = (0.0, 1.0, "binary")
            vars_[f"x_{i}_{t}"] = (0.0, big_m, "continuous")
            vars_[f"inv_{i}_{t}"] = (0.0, big_m, "continuous")
            vars_[f"unmet_{i}_{t}"] = (0.0, big_m, "continuous")
    return vars_


def structural_variables(inst) -> list[str]:
    return [f"y_{i}_{t}" for i in range(inst.n_items) for t in range(inst.n_periods)]


def to_assignment(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    return {f"y_{i}_{t}": float(bool(sol[i][t])) for i in range(inst.n_items) for t in range(inst.n_periods)}


def aux_values(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    n_items, n_periods = inst.n_items, inst.n_periods
    demand = inst.demand

    def build_model(minimize_inventory: bool, target_unmet: float | None = None):
        prob = pulp.LpProblem("clsp_aux_values", pulp.LpMinimize)
        x = [[pulp.LpVariable(f"x_{i}_{t}", lowBound=0) for t in range(n_periods)] for i in range(n_items)]
        inv = [[pulp.LpVariable(f"inv_{i}_{t}", lowBound=0) for t in range(n_periods)] for i in range(n_items)]
        unmet = [
            [pulp.LpVariable(f"unmet_{i}_{t}", lowBound=0, upBound=demand[i][t]) for t in range(n_periods)]
            for i in range(n_items)
        ]

        for t in range(n_periods):
            prob += (
                pulp.lpSum(x[i][t] for i in range(n_items))
                + pulp.lpSum(inst.setup_time[i] * (1.0 if sol[i][t] else 0.0) for i in range(n_items))
                <= inst.capacity[t]
            )
            for i in range(n_items):
                if not sol[i][t]:
                    prob += x[i][t] == 0

        for i in range(n_items):
            for t in range(n_periods):
                prev_inv = inv[i][t - 1] if t > 0 else 0
                prob += prev_inv + x[i][t] + unmet[i][t] == demand[i][t] + inv[i][t]

        if target_unmet is not None:
            prob += pulp.lpSum(unmet[i][t] for i in range(n_items) for t in range(n_periods)) == target_unmet
            if minimize_inventory:
                prob += pulp.lpSum(
                    inst.holding_cost[i] * inv[i][t] for i in range(n_items) for t in range(n_periods)
                )
            else:
                prob += 0
        else:
            prob += pulp.lpSum(unmet[i][t] for i in range(n_items) for t in range(n_periods))

        return prob, x, inv, unmet

    prob1, x1, inv1, unmet1 = build_model(minimize_inventory=False)
    prob1.solve(pulp.PULP_CBC_CMD(msg=False))
    status1 = pulp.LpStatus[prob1.status]
    if status1 not in {"Optimal", "Integer Feasible"}:
        min_unmet = float(sum(sum(row) for row in demand))
    else:
        min_unmet = float(
            pulp.value(pulp.lpSum(unmet1[i][t] for i in range(n_items) for t in range(n_periods))) or 0.0
        )

    prob2, x2, inv2, unmet2 = build_model(minimize_inventory=True, target_unmet=min_unmet)
    prob2.solve(pulp.PULP_CBC_CMD(msg=False))

    vals: dict[str, float] = {}
    for i in range(n_items):
        for t in range(n_periods):
            vals[f"x_{i}_{t}"] = float(pulp.value(x2[i][t]) or 0.0)
            vals[f"inv_{i}_{t}"] = float(pulp.value(inv2[i][t]) or 0.0)
            vals[f"unmet_{i}_{t}"] = float(pulp.value(unmet2[i][t]) or 0.0)
    return vals


def from_assignment(inst, x) -> "sol":
    n_items, n_periods = inst.n_items, inst.n_periods
    return tuple(tuple(bool(x.get(f"y_{i}_{t}", 0.0)) for t in range(n_periods)) for i in range(n_items))


def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    n_items, n_periods = inst.n_items, inst.n_periods
    fams: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "capacidad": [],
        "demanda": [],
        "link": [],
    }

    for t in range(n_periods):
        coeffs: dict[str, float] = {}
        for i in range(n_items):
            coeffs[f"x_{i}_{t}"] = coeffs.get(f"x_{i}_{t}", 0.0) + 1.0
            coeffs[f"y_{i}_{t}"] = coeffs.get(f"y_{i}_{t}", 0.0) + inst.setup_time[i]
        fams["capacidad"].append((coeffs, "<=", float(inst.capacity[t])))

    big_m = sum(max(0.0, d) for row in inst.demand for d in row)
    for i in range(n_items):
        for t in range(n_periods):
            fams["link"].append(({f"x_{i}_{t}": 1.0, f"y_{i}_{t}": -big_m}, "<=", 0.0))

    for i in range(n_items):
        for t in range(n_periods):
            coeffs = {f"x_{i}_{t}": 1.0, f"inv_{i}_{t}": -1.0}
            if t > 0:
                coeffs[f"inv_{i}_{t-1}"] = coeffs.get(f"inv_{i}_{t-1}", 0.0) + 1.0
            fams["demanda"].append((coeffs, ">=", float(inst.demand[i][t])))

    return fams


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
    n_items, n_periods = inst.n_items, inst.n_periods
    vars_ = [f"y_{i}_{t}" for i in range(n_items) for t in range(n_periods)]
    n_vars = len(vars_)
    if n_vars == 0:
        return {}

    max_group_size = max(1, n_vars // 3)
    n_groups = max(4, (n_vars + max_group_size - 1) // max_group_size)
    base = n_vars // n_groups
    rem = n_vars % n_groups

    groups: dict[str, list[str]] = {}
    start = 0
    for k in range(n_groups):
        size = base + (1 if k < rem else 0)
        if size == 0:
            continue
        groups[f"chunk_{k}"] = vars_[start : start + size]
        start += size

    return groups


# ---- vista constructiva ----
def _as_tuple_partial(partial):
    return tuple(tuple(row) for row in partial)


def empty_partial(inst):
    return tuple(tuple(None for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def _first_undecided(partial):
    for i, row in enumerate(partial):
        for t, v in enumerate(row):
            if v is None:
                return i, t
    return None


def _completion_setup(partial):
    return tuple(tuple(True if v is None else bool(v) for v in row) for row in partial)


@lru_cache(maxsize=8192)
def _is_completable_cached(inst_key, partial_tuple):
    n_items, n_periods, demand, capacity, setup_time, setup_cost, holding_cost = _key_to_data(inst_key)
    partial = partial_tuple
    setup = _completion_setup(partial)

    prob = pulp.LpProblem("clsp_completion", pulp.LpMinimize)
    x = [[pulp.LpVariable(f"x_{i}_{t}", lowBound=0) for t in range(n_periods)] for i in range(n_items)]
    inv = [[pulp.LpVariable(f"inv_{i}_{t}", lowBound=0) for t in range(n_periods)] for i in range(n_items)]
    unmet = [
        [pulp.LpVariable(f"unmet_{i}_{t}", lowBound=0, upBound=demand[i][t]) for t in range(n_periods)]
        for i in range(n_items)
    ]

    for t in range(n_periods):
        prob += (
            pulp.lpSum(x[i][t] for i in range(n_items))
            + pulp.lpSum(setup_time[i] * (1.0 if setup[i][t] else 0.0) for i in range(n_items))
            <= capacity[t]
        )
        for i in range(n_items):
            if not setup[i][t]:
                prob += x[i][t] == 0

    for i in range(n_items):
        for t in range(n_periods):
            prev_inv = inv[i][t - 1] if t > 0 else 0
            prob += prev_inv + x[i][t] + unmet[i][t] == demand[i][t] + inv[i][t]

    prob += pulp.lpSum(unmet[i][t] for i in range(n_items) for t in range(n_periods))
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    status = pulp.LpStatus[prob.status]
    if status not in {"Optimal", "Integer Feasible"}:
        return False

    total_unmet = float(pulp.value(pulp.lpSum(unmet[i][t] for i in range(n_items) for t in range(n_periods))))
    return total_unmet <= 1e-9


def _is_completable(inst, partial_tuple):
    return _is_completable_cached(_inst_key(inst), partial_tuple)


def candidates(inst, partial) -> list:
    partial = _as_tuple_partial(partial)
    nxt = _first_undecided(partial)
    if nxt is None:
        return []
    i, t = nxt

    out = []
    for val in (False, True):
        new_partial = tuple(
            tuple(val if (ii == i and tt == t) else partial[ii][tt] for tt in range(inst.n_periods))
            for ii in range(inst.n_items)
        )
        if _is_completable(inst, new_partial):
            out.append((i, t, val))
    return out


def apply_action(inst, partial, action):
    i, t, val = action
    return tuple(
        tuple(val if (ii == i and tt == t) else partial[ii][tt] for tt in range(inst.n_periods))
        for ii in range(inst.n_items)
    )


def is_complete(inst, partial) -> bool:
    return _first_undecided(_as_tuple_partial(partial)) is None


def to_solution(inst, partial):
    partial = _as_tuple_partial(partial)
    return _completion_setup(partial)


def complete_partial(inst, partial, rng):
    return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))
