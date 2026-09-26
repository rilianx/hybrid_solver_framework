from __future__ import annotations

from functools import lru_cache
from math import inf
from random import Random
from typing import Dict

from examples.cvrp.instance import CVRPInstance


# ---- caché por instancia ----
_INST_CACHE: dict[int, tuple[int, tuple[int, ...], tuple[float, ...], tuple[tuple[float, ...], ...], float]] = {}


def _inst_data(inst: CVRPInstance):
    key = id(inst)
    data = _INST_CACHE.get(key)
    if data is not None and data[0] == getattr(inst, "n_customers", None):
        return data[1], data[2], data[3], data[4]

    n = inst.n_customers
    customers = tuple(inst.customers)
    demand = tuple(float(inst.demand[i]) for i in range(n + 1))
    dist = tuple(tuple(float(inst.dist(i, j)) for j in range(n + 1)) for i in range(n + 1))
    cap = float(inst.capacity)
    data = (n, customers, demand, dist, cap)
    _INST_CACHE[key] = data
    return customers, demand, dist, cap


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


def _route_cost_from_dist(dist, route: tuple[int, ...]) -> float:
    if not route:
        return 0.0
    total = dist[0][route[0]]
    for i in range(len(route) - 1):
        total += dist[route[i]][route[i + 1]]
    total += dist[route[-1]][0]
    return total


@lru_cache(maxsize=None)
def _split_dp_cached(inst_id: int, tour: tuple[int, ...]):
    # inst_id is only used to key the cache; instance data are fetched from the live cache.
    inst = _INST_OBJ_CACHE[inst_id]
    _, demand, dist, cap = _inst_data(inst)

    n = len(tour)
    if n == 0:
        return (), 0.0

    big_penalty = 1e6
    dp = [inf] * (n + 1)
    prev = [-1] * (n + 1)
    dp[0] = 0.0

    for i in range(n):
        load = 0.0
        c0 = tour[i]
        cost = dist[0][c0] + dist[c0][0]
        prev_c = c0
        for j in range(i + 1, n + 1):
            c = tour[j - 1]
            if j > i + 1:
                cost += dist[prev_c][c] + dist[c][0] - dist[prev_c][0]
                prev_c = c
            load += demand[c]
            cand = dp[i] + cost + big_penalty * max(0.0, load - cap)
            if cand < dp[j]:
                dp[j] = cand
                prev[j] = i

    routes: list[tuple[int, ...]] = []
    j = n
    while j > 0:
        i = prev[j]
        if i < 0:
            break
        routes.append(tour[i:j])
        j = i
    routes.reverse()
    return tuple(routes), dp[n]


_INST_OBJ_CACHE: dict[int, CVRPInstance] = {}


def _split_dp(inst: CVRPInstance, tour: tuple[int, ...]):
    _INST_OBJ_CACHE[id(inst)] = inst
    return _split_dp_cached(id(inst), tour)


def violations(inst, sol) -> dict[str, float]:
    tour = _as_tour(sol)
    customers, demand, dist, cap = _inst_data(inst)
    customer_set = set(customers)

    counts = {c: 0 for c in customer_set}
    extra = 0
    for c in tour:
        if c in counts:
            counts[c] += 1
        else:
            extra += 1

    missing = sum(1 for c in customer_set if counts[c] == 0)
    duplicated = sum(max(0, counts[c] - 1) for c in customer_set)
    visita = float(missing + duplicated + extra)

    routes, _ = _split_dp(inst, tour)
    capacidad = 0.0
    for r in routes:
        load = 0.0
        for c in r:
            load += demand[c]
        capacidad += max(0.0, load - cap)

    return {"visita": float(visita), "capacidad": float(capacidad)}


def cost_terms(inst, sol) -> dict[str, float]:
    tour = _as_tour(sol)
    _, split_cost = _split_dp(inst, tour)

    vio = violations(inst, tour)
    penalty = 1e6 * vio["visita"] + 1e6 * vio["capacidad"]

    return {"distancia": float(split_cost + penalty)}


# ---- vista MIP ----
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


def _mip_route_cost(dist, route: tuple[int, ...]) -> float:
    if not route:
        return 0.0
    total = dist[0][route[0]]
    for i in range(len(route) - 1):
        total += dist[route[i]][route[i + 1]]
    total += dist[route[-1]][0]
    return total


@lru_cache(maxsize=None)
def _mip_split_dp_cached(inst_id: int, tour: tuple[int, ...]):
    inst = _INST_OBJ_CACHE[inst_id]
    _, demand, dist, cap = _inst_data(inst)

    n = len(tour)
    if n == 0:
        return (), 0.0

    big_penalty = 1e6
    dp = [inf] * (n + 1)
    prev = [-1] * (n + 1)
    dp[0] = 0.0

    for i in range(n):
        load = 0.0
        c0 = tour[i]
        cost = dist[0][c0] + dist[c0][0]
        prev_c = c0
        for j in range(i + 1, n + 1):
            c = tour[j - 1]
            if j > i + 1:
                cost += dist[prev_c][c] + dist[c][0] - dist[prev_c][0]
                prev_c = c
            load += demand[c]
            cand = dp[i] + cost + big_penalty * max(0.0, load - cap)
            if cand < dp[j]:
                dp[j] = cand
                prev[j] = i

    routes: list[tuple[int, ...]] = []
    j = n
    while j > 0:
        i = prev[j]
        if i < 0:
            break
        routes.append(tour[i:j])
        j = i
    routes.reverse()
    return tuple(routes), dp[n]


def _mip_split_dp(inst: CVRPInstance, tour: tuple[int, ...]):
    _INST_OBJ_CACHE[id(inst)] = inst
    return _mip_split_dp_cached(id(inst), tour)


def to_assignment(inst, sol) -> dict[str, float]:
    tour = tuple(int(c) for c in sol)
    routes, _ = _mip_split_dp(inst, tour)

    x = {name: 0.0 for name in structural_variables(inst)}
    for route in routes:
        if not route:
            continue
        x[f"x_0_{route[0]}"] = 1.0
        prev = 0
        for c in route:
            x[f"x_{prev}_{c}"] = 1.0
            prev = c
        x[f"x_{prev}_0"] = 1.0

    return x


def aux_values(inst, sol) -> dict[str, float]:
    tour = tuple(int(c) for c in sol)
    routes, _ = _mip_split_dp(inst, tour)

    _, demand, _, _ = _inst_data(inst)
    vals: dict[str, float] = {f"u_{c}": float(demand[c]) for c in inst.customers}
    for route in routes:
        load = 0.0
        for c in route:
            load += float(demand[c])
            vals[f"u_{c}"] = load
    return vals


def from_assignment(inst, x) -> "sol":
    n = inst.n_customers

    succ = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            if x.get(f"x_{i}_{j}", 0.0) > 0.5:
                succ[i] = j

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
    _, _, dist, _ = _inst_data(inst)
    coef: dict[str, float] = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                coef[f"x_{i}_{j}"] = float(dist[i][j])
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


# ---- vista constructiva ----
def empty_partial(inst):
    return ((), (), frozenset(inst.customers))


def _open_load(inst, open_route):
    _, demand, _, _ = _inst_data(inst)
    return sum(demand[c] for c in open_route)


def _route_delta(inst, open_route, c):
    _, _, dist, _ = _inst_data(inst)
    if not open_route:
        return 2.0 * dist[0][c]
    last = open_route[-1]
    return dist[last][c] + dist[c][0] - dist[last][0]


def candidates(inst, partial) -> list:
    built, open_route, remaining = partial
    if not remaining and not open_route:
        return []

    cand = []
    cap = inst.capacity
    load = _open_load(inst, open_route)

    feasible_adds = []
    for c in remaining:
        d = inst.demand[c]
        if load + d <= cap:
            feasible_adds.append(("add", c, _route_delta(inst, open_route, c)))

    if open_route:
        cand.extend(feasible_adds)
        cand.append(("close", None, 0.0))
    else:
        cand.extend(feasible_adds)

    return cand


def apply_action(inst, partial, action):
    built, open_route, remaining = partial
    kind = action[0]

    if kind == "add":
        c = int(action[1])
        if c not in remaining:
            return partial
        new_open = open_route + (c,)
        new_remaining = frozenset(x for x in remaining if x != c)
        return (built, new_open, new_remaining)

    if kind == "close":
        if not open_route:
            return partial
        return (built + (open_route,), (), remaining)

    return partial


def is_complete(inst, partial) -> bool:
    built, open_route, remaining = partial
    return not remaining and not open_route


def to_solution(inst, partial):
    built, open_route, remaining = partial
    if remaining or open_route:
        raise ValueError("partial solution is not complete")
    tour = tuple(c for route in built for c in route)
    return tour


def complete_partial(inst, partial, rng):
    built, open_route, remaining = partial

    routes = list(built)
    if open_route:
        routes.append(open_route)

    rem = list(remaining)

    while rem:
        current = []
        load = 0.0

        idxs = list(range(len(rem)))
        rng.shuffle(idxs)

        used = []
        for pos in idxs:
            c = rem[pos]
            d = inst.demand[c]
            if load + d <= inst.capacity:
                current.append(c)
                load += d
                used.append(pos)

        if not current:
            c = rem[0]
            current = [c]
            used = [0]

        routes.append(tuple(current))
        used_set = set(used)
        rem = [c for i, c in enumerate(rem) if i not in used_set]

    return tuple(c for route in routes for c in route)
