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
from math import inf

from examples.cvrp.instance import CVRPInstance


def _x_name(i: int, j: int) -> str:
    return f"x_{i}_{j}"


def _u_name(i: int) -> str:
    return f"u_{i}"


def variables(inst) -> dict[str, tuple[float, float, str]]:
    n = inst.n_customers
    vars_: dict[str, tuple[float, float, str]] = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                vars_[_x_name(i, j)] = (0.0, 1.0, "binary")
    q = float(inst.capacity)
    vars_[_u_name(0)] = (0.0, 0.0, "continuous")
    for i in inst.customers:
        vars_[_u_name(i)] = (float(inst.demand[i]), q, "continuous")
    return vars_


def structural_variables(inst) -> list[str]:
    n = inst.n_customers
    return [_x_name(i, j) for i in range(n + 1) for j in range(n + 1) if i != j]


def to_assignment(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    n = inst.n_customers
    x = {_x_name(i, j): 0.0 for i in range(n + 1) for j in range(n + 1) if i != j}
    u = {_u_name(i): 0.0 for i in range(n + 1)}

    for route in sol:
        prev = 0
        load = 0.0
        for c in route:
            if 1 <= c <= n:
                x[_x_name(prev, c)] = 1.0
                load += float(inst.demand[c])
                u[_u_name(c)] = load
                prev = c
        x[_x_name(prev, 0)] = 1.0

    return {**x, **u}


def aux_values(inst, sol) -> dict[str, float]:
    return {k: v for k, v in to_assignment(inst, sol).items() if k.startswith("u_")}


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
    fam: dict[str, list[tuple[dict[str, float], str, float]]] = {"visita": [], "capacidad": []}

    for c in inst.customers:
        in_coefs = {_x_name(i, c): 1.0 for i in range(n + 1) if i != c}
        out_coefs = {_x_name(c, j): 1.0 for j in range(n + 1) if j != c}
        fam["visita"].append((in_coefs, "==", 1.0))
        fam["visita"].append((out_coefs, "==", 1.0))

    q = float(inst.capacity)
    for i in inst.customers:
        fam["capacidad"].append(({_u_name(i): 1.0}, ">=", float(inst.demand[i])))
        fam["capacidad"].append(({_u_name(i): 1.0}, "<=", q))

    for i in inst.customers:
        for j in inst.customers:
            if i == j:
                continue
            fam["capacidad"].append(
                ({
                    _u_name(j): 1.0,
                    _u_name(i): -1.0,
                    _x_name(i, j): q,
                }, ">=", float(inst.demand[j]) - q)
            )

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
    n = inst.n_customers
    groups: dict[str, list[str]] = defaultdict(list)

    # Grupos por origen, repartidos en 4 bloques balanceados
    for i in range(n + 1):
        g = f"g{i % 4}"
        for j in range(n + 1):
            if i != j:
                groups[g].append(_x_name(i, j))

    return dict(groups)
