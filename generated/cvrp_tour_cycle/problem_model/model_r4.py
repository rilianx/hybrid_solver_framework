from __future__ import annotations

from math import inf
from random import Random
from typing import Iterable

from examples.cvrp.instance import CVRPInstance


def canonical(sol):
    if isinstance(sol, tuple):
        return sol
    return tuple(sol)


def trivial_solution(inst):
    return tuple(inst.customers)


def random_solution(inst, rng):
    customers = list(inst.customers)
    rng.shuffle(customers)
    return tuple(customers)


def from_answer(inst, answer):
    tour: list[int] = []
    seen = set()
    for route in answer:
        for c in route:
            c = int(c)
            tour.append(c)
            seen.add(c)
    return canonical(tuple(tour))


def _as_tour(sol) -> tuple[int, ...]:
    return canonical(sol)


def _route_cost(inst: CVRPInstance, route: tuple[int, ...]) -> float:
    if not route:
        return 0.0
    total = inst.dist(0, route[0])
    for i in range(len(route) - 1):
        total += inst.dist(route[i], route[i + 1])
    total += inst.dist(route[-1], 0)
    return total


def _split_dp(inst: CVRPInstance, tour: tuple[int, ...]):
    n = len(tour)
    if n == 0:
        return [], 0.0

    demand = inst.demand
    cap = inst.capacity

    # Precompute segment costs and excess loads.
    seg_cost = [[inf] * (n + 1) for _ in range(n)]
    seg_excess = [[0.0] * (n + 1) for _ in range(n)]

    big_penalty = 1e6
    for i in range(n):
        load = 0.0
        for j in range(i + 1, n + 1):
            load += demand[tour[j - 1]]
            route = tour[i:j]
            c = _route_cost(inst, route)
            excess = max(0.0, load - cap)
            seg_excess[i][j] = excess
            seg_cost[i][j] = c + big_penalty * excess

    dp = [inf] * (n + 1)
    prev = [-1] * (n + 1)
    dp[0] = 0.0

    for j in range(1, n + 1):
        best = inf
        best_i = -1
        for i in range(0, j):
            cand = dp[i] + seg_cost[i][j]
            if cand < best:
                best = cand
                best_i = i
        dp[j] = best
        prev[j] = best_i

    routes: list[tuple[int, ...]] = []
    j = n
    while j > 0:
        i = prev[j]
        if i < 0:
            break
        routes.append(tour[i:j])
        j = i
    routes.reverse()
    return routes, dp[n]


def violations(inst, sol) -> dict[str, float]:
    tour = _as_tour(sol)
    n = inst.n_customers
    customers = set(inst.customers)

    counts = {c: 0 for c in customers}
    extra = 0
    for c in tour:
        if c in counts:
            counts[c] += 1
        else:
            extra += 1

    missing = sum(1 for c in customers if counts[c] == 0)
    duplicated = sum(max(0, counts[c] - 1) for c in customers)
    visita = float(missing + duplicated + extra)

    routes, _ = _split_dp(inst, tour)
    capacidad = 0.0
    for r in routes:
        load = sum(inst.demand[c] for c in r)
        capacidad += max(0.0, load - inst.capacity)

    return {"visita": float(visita), "capacidad": float(capacidad)}


def cost_terms(inst, sol) -> dict[str, float]:
    tour = _as_tour(sol)
    routes, split_cost = _split_dp(inst, tour)

    # Penalize violations so infeasible solutions are always worse than feasible ones.
    vio = violations(inst, tour)
    penalty = 1e6 * vio["visita"] + 1e6 * vio["capacidad"]

    return {"distancia": float(split_cost + penalty)}


# ---- vista MIP ----
from math import inf
from typing import Dict

from examples.cvrp.instance import CVRPInstance


def variables(inst) -> dict[str, tuple[float, float, str]]:
    n = inst.n_customers
    out: dict[str, tuple[float, float, str]] = {}

    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                out[f"x_{i}_{j}"] = (0.0, 1.0, "binary")

    for i in inst.customers:
        out[f"u_{i}"] = (float(inst.demand[i]), float(inst.capacity), "continuous")

    return out


def structural_variables(inst) -> list[str]:
    n = inst.n_customers
    return [f"x_{i}_{j}" for i in range(n + 1) for j in range(n + 1) if i != j]


def _mip_route_cost(inst: CVRPInstance, route: tuple[int, ...]) -> float:
    if not route:
        return 0.0
    total = inst.dist(0, route[0])
    for i in range(len(route) - 1):
        total += inst.dist(route[i], route[i + 1])
    total += inst.dist(route[-1], 0)
    return total


def _mip_split_dp(inst: CVRPInstance, tour: tuple[int, ...]):
    n = len(tour)
    if n == 0:
        return [], 0.0

    demand = inst.demand
    cap = inst.capacity

    seg_cost = [[inf] * (n + 1) for _ in range(n)]
    big_penalty = 1e6
    for i in range(n):
        load = 0.0
        for j in range(i + 1, n + 1):
            load += demand[tour[j - 1]]
            route = tour[i:j]
            c = _mip_route_cost(inst, route)
            excess = max(0.0, load - cap)
            seg_cost[i][j] = c + big_penalty * excess

    dp = [inf] * (n + 1)
    prev = [-1] * (n + 1)
    dp[0] = 0.0

    for j in range(1, n + 1):
        best = inf
        best_i = -1
        for i in range(0, j):
            cand = dp[i] + seg_cost[i][j]
            if cand < best:
                best = cand
                best_i = i
        dp[j] = best
        prev[j] = best_i

    routes: list[tuple[int, ...]] = []
    j = n
    while j > 0:
        i = prev[j]
        if i < 0:
            break
        routes.append(tour[i:j])
        j = i
    routes.reverse()
    return routes, dp[n]


def to_assignment(inst, sol) -> dict[str, float]:
    tour = tuple(int(c) for c in sol)
    routes, _ = _mip_split_dp(inst, tour)

    x = {name: 0.0 for name in structural_variables(inst)}
    u = {f"u_{c}": float(inst.demand[c]) for c in inst.customers}

    for route in routes:
        if not route:
            continue
        x[f"x_0_{route[0]}"] = 1.0
        load = 0.0
        prev = 0
        for c in route:
            x[f"x_{prev}_{c}"] = 1.0
            load += float(inst.demand[c])
            u[f"u_{c}"] = load
            prev = c
        x[f"x_{prev}_0"] = 1.0

    out: Dict[str, float] = {}
    out.update(x)
    out.update(u)
    return out


def aux_values(inst, sol) -> dict[str, float]:
    # Return the auxiliary variables only, but fully and deterministically.
    tour = tuple(int(c) for c in sol)
    routes, _ = _mip_split_dp(inst, tour)

    vals: dict[str, float] = {f"u_{c}": float(inst.demand[c]) for c in inst.customers}
    for route in routes:
        load = 0.0
        for c in route:
            load += float(inst.demand[c])
            vals[f"u_{c}"] = load
    return vals


def from_assignment(inst, x) -> "sol":
    n = inst.n_customers

    succ = {}
    pred = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            if x.get(f"x_{i}_{j}", 0.0) > 0.5:
                succ[i] = j
                pred[j] = i

    routes: list[list[int]] = []
    used = set()

    starts = [j for j in inst.customers if x.get(f"x_0_{j}", 0.0) > 0.5]
    for start in starts:
        if start in used:
            continue
        route = []
        cur = start
        while cur != 0 and cur not in used:
            route.append(cur)
            used.add(cur)
            cur = succ.get(cur, 0)
        if route:
            routes.append(route)

    for c in inst.customers:
        if c not in used:
            routes.append([c])

    tour: list[int] = []
    for r in routes:
        tour.extend(r)
    return tuple(tour)


def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    n = inst.n_customers
    fam: dict[str, list[tuple[dict[str, float], str, float]]] = {"visita": [], "capacidad": []}

    for j in inst.customers:
        fam["visita"].append(({f"x_{i}_{j}": 1.0 for i in range(n + 1) if i != j}, "==", 1.0))
        fam["visita"].append(({f"x_{j}_{k}": 1.0 for k in range(n + 1) if k != j}, "==", 1.0))

    dep = {f"x_0_{j}": 1.0 for j in inst.customers}
    dep.update({f"x_{i}_0": -1.0 for i in inst.customers})
    fam["visita"].append((dep, "==", 0.0))

    Q = float(inst.capacity)
    for i in inst.customers:
        di = float(inst.demand[i])
        fam["capacidad"].append(({f"u_{i}": 1.0}, ">=", di))
        fam["capacidad"].append(({f"u_{i}": 1.0}, "<=", Q))
        fam["capacidad"].append(({f"u_{i}": 1.0, f"x_0_{i}": -Q}, ">=", di - Q))
        for j in inst.customers:
            if i == j:
                continue
            dj = float(inst.demand[j])
            fam["capacidad"].append(({f"u_{j}": 1.0, f"u_{i}": -1.0, f"x_{i}_{j}": -Q}, ">=", dj - Q))

    return fam


def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]:
    n = inst.n_customers
    coef: dict[str, float] = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                coef[f"x_{i}_{j}"] = float(inst.dist(i, j))
    return {"distancia": (coef, 0.0)}


def variable_groups(inst) -> dict[str, list[str]]:
    n = inst.n_customers
    groups: dict[str, list[str]] = {f"g{k}": [] for k in range(1, 5)}

    tails = list(range(n + 1))
    base = (n + 1) // 4
    rem = (n + 1) % 4
    start = 0
    tail_to_group = {}
    for k in range(4):
        size = base + (1 if k < rem else 0)
        for t in tails[start : start + size]:
            tail_to_group[t] = f"g{k + 1}"
        start += size

    for i in range(n + 1):
        gname = tail_to_group.get(i, "g4")
        for j in range(n + 1):
            if i != j:
                groups[gname].append(f"x_{i}_{j}")

    return groups
