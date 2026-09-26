from __future__ import annotations

from random import Random
from typing import Any

from examples.cvrp.instance import CVRPInstance


def canonical(sol):
    routes = []
    for route in sol:
        if route:
            routes.append(tuple(int(c) for c in route))
    routes.sort(key=lambda r: r[0])
    return tuple(routes)


def trivial_solution(inst: CVRPInstance):
    return tuple((c,) for c in inst.customers)


def random_solution(inst: CVRPInstance, rng: Random):
    customers = list(inst.customers)
    rng.shuffle(customers)

    routes = []
    current = []
    current_load = 0.0
    for c in customers:
        d = inst.demand[c]
        if current and current_load + d > inst.capacity and rng.random() < 0.8:
            routes.append(tuple(current))
            current = [c]
            current_load = d
        else:
            current.append(c)
            current_load += d

    if current:
        routes.append(tuple(current))

    return canonical(routes)


def from_answer(inst: CVRPInstance, answer):
    return canonical(tuple(tuple(int(c) for c in route) for route in answer))


def violations(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)

    counts = [0] * (inst.n_customers + 1)
    for route in sol:
        for c in route:
            if 1 <= c <= inst.n_customers:
                counts[c] += 1
            else:
                counts[0] += 1  # out of range, counts as invalid extra visit

    visita = 0.0
    for c in inst.customers:
        visita += abs(counts[c] - 1)

    # Any invalid customer index is treated as a violation of visita as well
    visita += float(counts[0])

    capacidad = 0.0
    for route in sol:
        load = sum(inst.demand[c] for c in route if 1 <= c <= inst.n_customers)
        capacidad += max(0.0, load - inst.capacity)

    return {"visita": float(visita), "capacidad": float(capacidad)}


def cost_terms(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)

    distance = 0.0
    for route in sol:
        prev = 0
        for c in route:
            if 1 <= c <= inst.n_customers:
                distance += inst.dist(prev, c)
                prev = c
        distance += inst.dist(prev, 0)

    v = violations(inst, sol)
    penalty_scale = 1.0 + 1000.0 * (inst.n_customers + 1) * max(
        (inst.dist(i, j) for i in range(inst.n_customers + 1) for j in range(inst.n_customers + 1)),
        default=1.0,
    )
    penalized_distance = distance + penalty_scale * (v["visita"] + v["capacidad"])
    return {"distancia": float(penalized_distance)}


# ---- vista MIP ----
from collections import defaultdict

from examples.cvrp.instance import CVRPInstance


def canonical(sol):
    routes = []
    for route in sol:
        if route:
            routes.append(tuple(int(c) for c in route))
    routes.sort(key=lambda r: r[0])
    return tuple(routes)


def _x_name(i: int, j: int) -> str:
    return f"x_{i}_{j}"


def _f_name(i: int, j: int) -> str:
    return f"f_{i}_{j}"


def variables(inst) -> dict[str, tuple[float, float, str]]:
    n = inst.n_customers
    vars_: dict[str, tuple[float, float, str]] = {}

    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                vars_[_x_name(i, j)] = (0.0, 1.0, "binary")
                vars_[_f_name(i, j)] = (0.0, float(inst.capacity), "continuous")

    return vars_


def structural_variables(inst) -> list[str]:
    n = inst.n_customers
    return [_x_name(i, j) for i in range(n + 1) for j in range(n + 1) if i != j]


def to_assignment(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    n = inst.n_customers
    q = float(inst.capacity)

    x = {_x_name(i, j): 0.0 for i in range(n + 1) for j in range(n + 1) if i != j}
    f = {_f_name(i, j): 0.0 for i in range(n + 1) for j in range(n + 1) if i != j}

    for route in sol:
        prev = 0
        remaining = sum(float(inst.demand[c]) for c in route if 1 <= c <= n)
        for c in route:
            if 1 <= c <= n:
                x[_x_name(prev, c)] = 1.0
                f[_f_name(prev, c)] = remaining
                remaining -= float(inst.demand[c])
                prev = c
        x[_x_name(prev, 0)] = 1.0
        f[_f_name(prev, 0)] = 0.0

    return {**x, **f}


def aux_values(inst, sol) -> dict[str, float]:
    ass = to_assignment(inst, sol)
    return {k: v for k, v in ass.items() if k.startswith("f_")}


def from_assignment(inst, x) -> tuple[tuple[int, ...], ...]:
    n = inst.n_customers
    succ = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j and float(x.get(_x_name(i, j), 0.0)) > 0.5:
                succ[i] = j

    routes = []
    starts = [j for j in range(1, n + 1) if float(x.get(_x_name(0, j), 0.0)) > 0.5]
    starts.sort()
    used = set()

    for s in starts:
        if s in used:
            continue
        route = []
        cur = s
        seen = set()
        while cur != 0 and cur not in seen:
            seen.add(cur)
            route.append(cur)
            used.add(cur)
            cur = succ.get(cur, 0)
        if route:
            routes.append(tuple(route))

    routes.sort(key=lambda r: r[0])
    return tuple(routes)


def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    n = inst.n_customers
    q = float(inst.capacity)
    total_demand = float(sum(inst.demand[c] for c in inst.customers))

    fam: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "visita": [],
        "capacidad": [],
    }

    # Each customer has exactly one incoming and one outgoing arc
    for c in inst.customers:
        in_coefs = {_x_name(i, c): 1.0 for i in range(n + 1) if i != c}
        out_coefs = {_x_name(c, j): 1.0 for j in range(n + 1) if j != c}
        fam["visita"].append((in_coefs, "==", 1.0))
        fam["visita"].append((out_coefs, "==", 1.0))

    # Flow conservation for delivered demand
    # sum_i f_{i,j} - sum_k f_{j,k} = demand[j] for customers
    for j in inst.customers:
        coefs: dict[str, float] = {}
        for i in range(n + 1):
            if i != j:
                coefs[_f_name(i, j)] = coefs.get(_f_name(i, j), 0.0) + 1.0
        for k in range(n + 1):
            if k != j:
                coefs[_f_name(j, k)] = coefs.get(_f_name(j, k), 0.0) - 1.0
        fam["capacidad"].append((coefs, "==", float(inst.demand[j])))

    # Depot balance: outflow - inflow = total demand
    depot_coefs: dict[str, float] = {}
    for k in range(1, n + 1):
        depot_coefs[_f_name(0, k)] = depot_coefs.get(_f_name(0, k), 0.0) + 1.0
        depot_coefs[_f_name(k, 0)] = depot_coefs.get(_f_name(k, 0), 0.0) - 1.0
    fam["capacidad"].append((depot_coefs, "==", total_demand))

    # Capacity on each arc: f_ij <= q x_ij
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                fam["capacidad"].append(({_f_name(i, j): 1.0, _x_name(i, j): -q}, "<=", 0.0))

    return fam


def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]:
    n = inst.n_customers
    coefs: dict[str, float] = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                coefs[_x_name(i, j)] = float(inst.dist(i, j))
    return {"distancia": (coefs, 0.0)}


def variable_groups(inst) -> dict[str, list[str]]:
    xs = structural_variables(inst)
    groups: dict[str, list[str]] = defaultdict(list)

    # Round-robin partition into 4 balanced blocks
    for idx, name in enumerate(xs):
        groups[f"g{idx % 4}"].append(name)

    # Ensure at least 4 groups exist
    for k in range(4):
        groups.setdefault(f"g{k}", [])

    return dict(groups)
