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


# ---- vista MIP ----
from math import ceil

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


def _canonical(sol):
    return tuple(tuple(bool(v) for v in row) for row in sol)


def _solve_aux_values(inst: CLSPInstance, y):
    n_items, n_periods = inst.n_items, inst.n_periods

    def build(stage2: bool, min_short: float | None = None):
        prob = pulp.LpProblem("clsp_aux", pulp.LpMinimize)
        x = pulp.LpVariable.dicts("x", (range(n_items), range(n_periods)), lowBound=0)
        inv = pulp.LpVariable.dicts("inv", (range(n_items), range(n_periods)), lowBound=0)
        short = pulp.LpVariable.dicts("short", (range(n_items), range(n_periods)), lowBound=0)

        for i in range(n_items):
            for t in range(n_periods):
                prev_inv = 0 if t == 0 else inv[i][t - 1]
                prob += prev_inv + x[i][t] + short[i][t] == float(inst.demand[i][t]) + inv[i][t]
                prob += x[i][t] <= float(inst.capacity[t]) * (1.0 if y[i][t] else 0.0)

        for t in range(n_periods):
            prob += (
                pulp.lpSum(x[i][t] for i in range(n_items))
                + pulp.lpSum(_setup_time(inst, i) * (1.0 if y[i][t] else 0.0) for i in range(n_items))
                <= float(inst.capacity[t])
            )

        if stage2:
            prob += pulp.lpSum(short[i][t] for i in range(n_items) for t in range(n_periods)) == float(min_short)
            prob += pulp.lpSum(_holding_cost(inst, i) * inv[i][t] for i in range(n_items) for t in range(n_periods))
        else:
            prob += pulp.lpSum(short[i][t] for i in range(n_items) for t in range(n_periods))

        return prob, x, inv, short

    prob1, x1, inv1, short1 = build(stage2=False)
    prob1.solve(pulp.PULP_CBC_CMD(msg=False))
    min_short = float(pulp.value(prob1.objective) or 0.0)

    prob2, x2, inv2, short2 = build(stage2=True, min_short=min_short)
    prob2.solve(pulp.PULP_CBC_CMD(msg=False))

    x_val = {f"x[{i},{t}]": float(pulp.value(x2[i][t]) or 0.0) for i in range(n_items) for t in range(n_periods)}
    inv_val = {f"inv[{i},{t}]": float(pulp.value(inv2[i][t]) or 0.0) for i in range(n_items) for t in range(n_periods)}
    return x_val, inv_val


def variables(inst) -> dict[str, tuple[float, float, str]]:
    vars_ = {}
    for i in range(inst.n_items):
        total_d = float(sum(inst.demand[i][t] for t in range(inst.n_periods)))
        for t in range(inst.n_periods):
            x_ub = min(float(inst.capacity[t]), total_d)
            inv_ub = float(sum(inst.demand[i][k] for k in range(t, inst.n_periods)))
            vars_[f"y[{i},{t}]"] = (0.0, 1.0, "binary")
            vars_[f"x[{i},{t}]"] = (0.0, x_ub, "continuous")
            vars_[f"inv[{i},{t}]"] = (0.0, inv_ub, "continuous")
    return vars_


def structural_variables(inst) -> list[str]:
    return [f"y[{i},{t}]" for i in range(inst.n_items) for t in range(inst.n_periods)]


def to_assignment(inst, sol) -> dict[str, float]:
    y = _canonical(sol)
    return {f"y[{i},{t}]": float(y[i][t]) for i in range(inst.n_items) for t in range(inst.n_periods)}


def aux_values(inst, sol) -> dict[str, float]:
    y = _canonical(sol)
    x_val, inv_val = _solve_aux_values(inst, y)
    out = {}
    out.update(x_val)
    out.update(inv_val)
    return out


def from_assignment(inst, x) -> "sol":
    return _canonical(
        tuple(
            tuple(bool(x.get(f"y[{i},{t}]", 0.0) > 0.5) for t in range(inst.n_periods))
            for i in range(inst.n_items)
        )
    )


def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    fam = {"demanda": [], "capacidad": [], "setup_link": []}
    n_items, n_periods = inst.n_items, inst.n_periods

    for i in range(n_items):
        for t in range(n_periods):
            coeffs = {f"inv[{i},{t}]": 1.0, f"x[{i},{t}]": 1.0}
            if t > 0:
                coeffs[f"inv[{i},{t-1}]"] = -1.0
            fam["demanda"].append((coeffs, "==", float(inst.demand[i][t])))

    for t in range(n_periods):
        coeffs = {}
        for i in range(n_items):
            coeffs[f"x[{i},{t}]"] = 1.0
            coeffs[f"y[{i},{t}]"] = _setup_time(inst, i)
        fam["capacidad"].append((coeffs, "<=", float(inst.capacity[t])))

    for i in range(n_items):
        total_d = float(sum(inst.demand[i][k] for k in range(n_periods)))
        for t in range(n_periods):
            fam["setup_link"].append(
                ({f"x[{i},{t}]": 1.0, f"y[{i},{t}]": -min(float(inst.capacity[t]), total_d)}, "<=", 0.0)
            )

    return fam


def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]:
    setup_coeffs = {}
    inv_coeffs = {}
    for i in range(inst.n_items):
        for t in range(inst.n_periods):
            setup_coeffs[f"y[{i},{t}]"] = _setup_cost(inst, i)
            inv_coeffs[f"inv[{i},{t}]"] = _holding_cost(inst, i)
    return {
        "setup": (setup_coeffs, 0.0),
        "inventario": (inv_coeffs, 0.0),
    }


def variable_groups(inst) -> dict[str, list[str]]:
    ys = structural_variables(inst)
    n_groups = 4
    groups = {f"g{k}": [] for k in range(n_groups)}
    periods = list(range(inst.n_periods))
    chunk = max(1, ceil(len(periods) / n_groups))
    for idx, t0 in enumerate(range(0, len(periods), chunk)):
        g = min(idx, n_groups - 1)
        for t in periods[t0 : t0 + chunk]:
            for i in range(inst.n_items):
                groups[f"g{g}"].append(f"y[{i},{t}]")
    assigned = {v for vals in groups.values() for v in vals}
    missing = [v for v in ys if v not in assigned]
    for j, v in enumerate(missing):
        groups[f"g{j % n_groups}"].append(v)
    return groups
