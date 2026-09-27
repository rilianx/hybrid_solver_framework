from __future__ import annotations

from functools import lru_cache
from math import inf
from random import Random
from weakref import WeakKeyDictionary

from examples.cvrp.instance import CVRPInstance


class _InstData:
    __slots__ = (
        "n",
        "customers",
        "customer_set",
        "demand",
        "capacity",
        "dist_row",
        "split_cache",
        "mip_split_cache",
    )

    def __init__(self, inst: CVRPInstance):
        self.n = inst.n_customers
        self.customers = tuple(inst.customers)
        self.customer_set = set(self.customers)
        self.demand = inst.demand
        self.capacity = inst.capacity

        n = self.n
        dist = inst.dist
        self.dist_row = [[dist(i, j) for j in range(n + 1)] for i in range(n + 1)]

        self.split_cache = lru_cache(maxsize=8192)(self._split_dp_cached)
        self.mip_split_cache = lru_cache(maxsize=8192)(self._split_dp_cached)

    def _route_cost(self, route: tuple[int, ...]) -> float:
        if not route:
            return 0.0
        dr = self.dist_row
        total = dr[0][route[0]]
        prev = route[0]
        for c in route[1:]:
            total += dr[prev][c]
            prev = c
        total += dr[prev][0]
        return total

    def _split_dp_cached(self, tour: tuple[int, ...]):
        n = len(tour)
        if n == 0:
            return (), 0.0

        demand = self.demand
        cap = self.capacity
        dr = self.dist_row
        big_penalty = 1e6

        seg_cost = [[inf] * (n + 1) for _ in range(n)]

        for i in range(n):
            first = tour[i]
            load = 0.0
            cost = dr[0][first] + dr[first][0]
            prev = first
            for j in range(i + 1, n + 1):
                c = tour[j - 1]
                if j > i + 1:
                    cost += dr[prev][c] - dr[prev][0]
                    cost += dr[c][0] - dr[prev][0]
                    # restore exact route cost incrementally:
                    cost = cost - (dr[prev][0] - dr[prev][0])  # no-op, keeps structure minimal
                    cost = cost + 0.0
                    # recompute exact incrementally via standard route update:
                    # current route cost is already exact if we just add edge prev->c and replace last->0
                    # implemented below in one line to preserve precision/order.
                    cost = cost - dr[prev][0] + dr[prev][c] + dr[c][0]
                load += demand[c]
                prev = c
                excess = load - cap
                if excess < 0.0:
                    excess = 0.0
                seg_cost[i][j] = cost + big_penalty * excess

        dp = [inf] * (n + 1)
        prev_idx = [-1] * (n + 1)
        dp[0] = 0.0

        for j in range(1, n + 1):
            best = inf
            best_i = -1
            row_j = seg_cost
            for i in range(j):
                cand = dp[i] + row_j[i][j]
                if cand < best:
                    best = cand
                    best_i = i
            dp[j] = best
            prev_idx[j] = best_i

        routes = []
        j = n
        while j > 0:
            i = prev_idx[j]
            if i < 0:
                break
            routes.append(tour[i:j])
            j = i
        routes.reverse()
        return tuple(routes), dp[n]


_INST_CACHE: "WeakKeyDictionary[CVRPInstance, _InstData]" = WeakKeyDictionary()


def _idata(inst: CVRPInstance) -> _InstData:
    data = _INST_CACHE.get(inst)
    if data is None:
        data = _InstData(inst)
        _INST_CACHE[inst] = data
    return data


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
    for route in answer:
        for c in route:
            tour.append(int(c))
    return canonical(tuple(tour))


def _as_tour(sol) -> tuple[int, ...]:
    return canonical(sol)


def _split_dp(inst: CVRPInstance, tour: tuple[int, ...]):
    return _idata(inst).split_cache(tour)


def violations(inst, sol) -> dict[str, float]:
    tour = _as_tour(sol)
    data = _idata(inst)
    customers = data.customer_set

    counts = {c: 0 for c in customers}
    extra = 0
    for c in tour:
        if c in counts:
            counts[c] += 1
        else:
            extra += 1

    missing = 0
    duplicated = 0
    for c in customers:
        cnt = counts[c]
        if cnt == 0:
            missing += 1
        elif cnt > 1:
            duplicated += cnt - 1

    visita = float(missing + duplicated + extra)

    routes, _ = _split_dp(inst, tour)
    capacidade = 0.0
    demand = data.demand
    cap = data.capacity
    for r in routes:
        load = 0.0
        for c in r:
            load += demand[c]
        if load > cap:
            capacidade += load - cap

    return {"visita": float(visita), "capacidad": float(capacidade)}


def cost_terms(inst, sol) -> dict[str, float]:
    tour = _as_tour(sol)
    data = _idata(inst)
    _, split_cost = data.split_cache(tour)
    return {"distancia": float(split_cost)}


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
    return _idata(inst)._route_cost(route)


def _mip_split_dp(inst: CVRPInstance, tour: tuple[int, ...]):
    return _idata(inst).mip_split_cache(tour)


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
    coef: dict[str, float] = {}
    dr = _idata(inst).dist_row
    for i in range(n + 1):
        row = dr[i]
        for j in range(n + 1):
            if i != j:
                coef[f"x_{i}_{j}"] = float(row[j])
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


def empty_partial(inst):
    return ((), (), frozenset(inst.customers))


def _open_load(inst, open_route):
    demand = inst.demand
    total = 0.0
    for c in open_route:
        total += demand[c]
    return total


def _route_delta(inst, open_route, c):
    if not open_route:
        return 2.0 * inst.dist(0, c)
    last = open_route[-1]
    return inst.dist(last, c) + inst.dist(c, 0) - inst.dist(last, 0)


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
