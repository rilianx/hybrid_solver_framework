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


# ---- vista MIP ----
from typing import Dict, List, Tuple

from examples.lotsizing.instance import CLSPInstance


def variables(inst) -> dict[str, tuple[float, float, str]]:
    vars_: dict[str, tuple[float, float, str]] = {}
    n_items, n_periods = inst.n_items, inst.n_periods

    for i in range(n_items):
        for t in range(n_periods):
            vars_[f"y_{i}_{t}"] = (0.0, 1.0, "binary")
            vars_[f"x_{i}_{t}"] = (0.0, float(inst.capacity[t]), "continuous")
            vars_[f"inv_{i}_{t}"] = (0.0, float("inf"), "continuous")
    return vars_


def structural_variables(inst) -> list[str]:
    return [f"y_{i}_{t}" for i in range(inst.n_items) for t in range(inst.n_periods)]


def to_assignment(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    return {
        f"y_{i}_{t}": 1.0 if sol[i][t] else 0.0
        for i in range(inst.n_items)
        for t in range(inst.n_periods)
    }


def aux_values(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    _, _, _ = _solve_plan(inst, sol)  # ensure cache warm / consistency

    n_items, n_periods = inst.n_items, inst.n_periods
    y = sol

    # Recompute the optimal production/inventory plan from the cached heuristic view.
    # The helper returns only cost terms, so we solve again here by reusing its internal
    # cached model structure through the same routine.
    import pulp  # local import to keep the public surface minimal

    def build_problem(stage: int, unmet_limit: float | None = None):
        prob = pulp.LpProblem("CLSP_aux_values", pulp.LpMinimize)
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

        for i in range(n_items):
            for t in range(n_periods):
                lhs = x[(i, t)] + short[(i, t)]
                if t == 0:
                    prob += lhs == inst.demand[i][t] + inv[(i, t)]
                else:
                    prob += inv[(i, t - 1)] + lhs == inst.demand[i][t] + inv[(i, t)]

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

    prob1, x1, inv1, short1 = build_problem(stage=1)
    prob1.solve(pulp.PULP_CBC_CMD(msg=False))
    unmet = pulp.value(pulp.lpSum(short1[(i, t)] for i in range(n_items) for t in range(n_periods)))
    if unmet is None:
        unmet = float("inf")

    prob2, x2, inv2, short2 = build_problem(stage=2, unmet_limit=unmet)
    prob2.solve(pulp.PULP_CBC_CMD(msg=False))

    vals: dict[str, float] = {}
    for i in range(n_items):
        for t in range(n_periods):
            xv = pulp.value(x2[(i, t)])
            iv = pulp.value(inv2[(i, t)])
            vals[f"x_{i}_{t}"] = 0.0 if xv is None else float(xv)
            vals[f"inv_{i}_{t}"] = 0.0 if iv is None else float(iv)
    return vals


def from_assignment(inst, x) -> "sol":
    return tuple(
        tuple(bool(x.get(f"y_{i}_{t}", 0.0)) for t in range(inst.n_periods))
        for i in range(inst.n_items)
    )


def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    fam: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "demanda": [],
        "capacidad": [],
        "enlace": [],
    }

    n_items, n_periods = inst.n_items, inst.n_periods

    for i in range(n_items):
        for t in range(n_periods):
            coeffs: dict[str, float] = {f"x_{i}_{t}": 1.0, f"inv_{i}_{t}": -1.0}
            if t > 0:
                coeffs[f"inv_{i}_{t-1}"] = 1.0
            fam["demanda"].append((coeffs, ">=", float(inst.demand[i][t])))

    for t in range(n_periods):
        coeffs = {f"x_{i}_{t}": 1.0 for i in range(n_items)}
        for i in range(n_items):
            coeffs[f"y_{i}_{t}"] = float(inst.setup_time[i])
        fam["capacidad"].append((coeffs, "<=", float(inst.capacity[t])))

    for i in range(n_items):
        for t in range(n_periods):
            fam["enlace"].append(
                ({f"x_{i}_{t}": 1.0, f"y_{i}_{t}": -float(inst.capacity[t])}, "<=", 0.0)
            )

    return fam


def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]:
    setup = {f"y_{i}_{t}": float(inst.setup_cost[i]) for i in range(inst.n_items) for t in range(inst.n_periods)}
    inventory = {f"inv_{i}_{t}": float(inst.holding_cost[i]) for i in range(inst.n_items) for t in range(inst.n_periods)}
    return {"setup": (setup, 0.0), "inventario": (inventory, 0.0)}


def variable_groups(inst) -> dict[str, list[str]]:
    n_periods = inst.n_periods
    groups: dict[str, list[str]] = {f"periodo_{k}": [] for k in range(4)}
    for t in range(n_periods):
        g = t % 4
        groups[f"periodo_{g}"].extend(f"y_{i}_{t}" for i in range(inst.n_items))
    return groups
