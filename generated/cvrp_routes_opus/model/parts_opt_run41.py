from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from random import Random
from typing import Any

from examples.cvrp.instance import CVRPInstance


# ---------------------------------------------------------------------
# Utilidades comunes y cachés por instancia
# ---------------------------------------------------------------------

def canonical(sol):
    routes = []
    append = routes.append
    for route in sol:
        if route:
            append(tuple(int(c) for c in route))
    routes.sort(key=lambda r: r[0])
    return tuple(routes)


def _inst_key(inst: CVRPInstance) -> int:
    return id(inst)


_INST_CACHE: dict[int, dict[str, Any]] = {}


def _get_inst_data(inst: CVRPInstance) -> dict[str, Any]:
    key = id(inst)
    data = _INST_CACHE.get(key)
    if data is None:
        n = int(inst.n_customers)
        customers = tuple(int(c) for c in inst.customers)
        demand = [0.0] * (n + 1)
        for c in customers:
            demand[c] = float(inst.demand[c])

        dist_mat = [[0.0] * (n + 1) for _ in range(n + 1)]
        max_dist = 1.0
        for i in range(n + 1):
            row = dist_mat[i]
            for j in range(n + 1):
                if i != j:
                    d = float(inst.dist(i, j))
                    row[j] = d
                    if d > max_dist:
                        max_dist = d

        data = {
            "n": n,
            "customers": customers,
            "demand": tuple(demand),
            "capacity": float(inst.capacity),
            "dist": tuple(tuple(r) for r in dist_mat),
            "max_dist": max_dist,
            "penalty_scale": 1.0 + 1000.0 * (n + 1) * max_dist,
            "total_demand": float(sum(demand)),
        }
        _INST_CACHE[key] = data
    return data


@lru_cache(maxsize=200000)
def _evaluate_cached(inst_key: int, sol: tuple[tuple[int, ...], ...]) -> tuple[float, float, float, float]:
    inst = _INST_CACHE[inst_key]["_inst"]
    data = _INST_CACHE[inst_key]
    n = data["n"]
    demand = data["demand"]
    capacity = data["capacity"]
    dist = data["dist"]
    penalty_scale = data["penalty_scale"]

    counts = [0] * (n + 1)
    visita_invalid = 0.0
    capacidad = 0.0
    distance = 0.0

    for route in sol:
        prev = 0
        load = 0.0
        for c in route:
            if 1 <= c <= n:
                counts[c] += 1
                d = demand[c]
                load += d
                distance += dist[prev][c]
                prev = c
            else:
                visita_invalid += 1.0
        distance += dist[prev][0]
        if load > capacity:
            capacidad += load - capacity

    visita = visita_invalid
    for c in range(1, n + 1):
        visita += abs(counts[c] - 1)

    penalized_distance = distance + penalty_scale * (visita + capacidad)
    return visita, capacidad, distance, penalized_distance


def _prepare_inst_cache(inst: CVRPInstance) -> int:
    key = id(inst)
    data = _INST_CACHE.get(key)
    if data is None:
        data = _get_inst_data(inst)
    if "_inst" not in data:
        data["_inst"] = inst
    return key


# ---------------------------------------------------------------------
# Vista evaluación
# ---------------------------------------------------------------------

def trivial_solution(inst: CVRPInstance):
    return tuple((c,) for c in inst.customers)


def random_solution(inst: CVRPInstance, rng: Random):
    data = _get_inst_data(inst)
    customers = list(data["customers"])
    rng.shuffle(customers)

    routes = []
    current = []
    current_load = 0.0
    capacity = data["capacity"]
    demand = data["demand"]

    for c in customers:
        d = demand[c]
        if current and current_load + d > capacity and rng.random() < 0.8:
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
    key = _prepare_inst_cache(inst)
    visita, capacidad, _, _ = _evaluate_cached(key, sol)
    return {"visita": float(visita), "capacidad": float(capacidad)}


def cost_terms(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)
    key = _prepare_inst_cache(inst)
    _, _, _, penalized_distance = _evaluate_cached(key, sol)
    return {"distancia": float(penalized_distance)}


# ---- vista MIP ----

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
    x = {_x_name(i, j): 0.0 for i in range(n + 1) for j in range(n + 1) if i != j}

    for route in sol:
        prev = 0
        for c in route:
            if 1 <= c <= n:
                x[_x_name(prev, c)] = 1.0
                prev = c
        x[_x_name(prev, 0)] = 1.0

    return x


def aux_values(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    n = inst.n_customers
    data = _get_inst_data(inst)
    demand = data["demand"]

    f = {_f_name(i, j): 0.0 for i in range(n + 1) for j in range(n + 1) if i != j}

    for route in sol:
        prev = 0
        remaining = 0.0
        for c in route:
            if 1 <= c <= n:
                remaining += demand[c]
        for c in route:
            if 1 <= c <= n:
                f[_f_name(prev, c)] = remaining
                remaining -= demand[c]
                prev = c
        f[_f_name(prev, 0)] = 0.0

    return f


def from_assignment(inst, x) -> tuple[tuple[int, ...], ...]:
    n = inst.n_customers
    succ = {}
    get = x.get
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j and float(get(_x_name(i, j), 0.0)) > 0.5:
                succ[i] = j

    routes = []
    starts = [j for j in range(1, n + 1) if float(get(_x_name(0, j), 0.0)) > 0.5]
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
    data = _get_inst_data(inst)
    total_demand = data["total_demand"]

    fam: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "visita": [],
        "capacidad": [],
    }

    for c in inst.customers:
        in_coefs = {_x_name(i, c): 1.0 for i in range(n + 1) if i != c}
        out_coefs = {_x_name(c, j): 1.0 for j in range(n + 1) if j != c}
        fam["visita"].append((in_coefs, "==", 1.0))
        fam["visita"].append((out_coefs, "==", 1.0))

    for j in inst.customers:
        coefs: dict[str, float] = {}
        for i in range(n + 1):
            if i != j:
                coefs[_f_name(i, j)] = coefs.get(_f_name(i, j), 0.0) + 1.0
        for k in range(n + 1):
            if k != j:
                coefs[_f_name(j, k)] = coefs.get(_f_name(j, k), 0.0) - 1.0
        fam["capacidad"].append((coefs, "==", float(inst.demand[j])))

    depot_coefs: dict[str, float] = {}
    for k in range(1, n + 1):
        depot_coefs[_f_name(0, k)] = depot_coefs.get(_f_name(0, k), 0.0) + 1.0
        depot_coefs[_f_name(k, 0)] = depot_coefs.get(_f_name(k, 0), 0.0) - 1.0
    fam["capacidad"].append((depot_coefs, "==", total_demand))

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

    for idx, name in enumerate(xs):
        groups[f"g{idx % 4}"].append(name)

    for k in range(4):
        groups.setdefault(f"g{k}", [])

    return dict(groups)


# ---- vista constructiva ----

@dataclass(frozen=True)
class _Partial:
    finished: tuple[tuple[int, ...], ...]
    current: tuple[int, ...]
    remaining: tuple[int, ...]


def empty_partial(inst):
    return _Partial(finished=tuple(), current=tuple(), remaining=tuple(inst.customers))


def candidates(inst, partial) -> list:
    if not isinstance(partial, _Partial):
        partial = _Partial(
            finished=tuple(),
            current=tuple(),
            remaining=tuple(sorted(int(c) for c in partial)),
        )
    return list(partial.remaining)


def apply_action(inst, partial, action):
    if not isinstance(partial, _Partial):
        partial = _Partial(
            finished=tuple(),
            current=tuple(),
            remaining=tuple(sorted(int(c) for c in partial)),
        )

    c = int(action)
    if c not in partial.remaining:
        raise ValueError("acción inválida: el cliente ya no está disponible")

    remaining = tuple(x for x in partial.remaining if x != c)

    if not partial.current:
        current = (c,)
        finished = partial.finished
    else:
        load = sum(inst.demand[i] for i in partial.current)
        if load + inst.demand[c] <= inst.capacity:
            current = partial.current + (c,)
            finished = partial.finished
        else:
            finished = partial.finished + (partial.current,)
            current = (c,)

    return _Partial(finished=finished, current=current, remaining=remaining)


def is_complete(inst, partial) -> bool:
    if not isinstance(partial, _Partial):
        return len(partial) == 0
    return len(partial.remaining) == 0


def to_solution(inst, partial):
    if not isinstance(partial, _Partial):
        return canonical(partial)

    routes = list(partial.finished)
    if partial.current:
        routes.append(partial.current)
    return canonical(tuple(routes))


def complete_partial(inst, partial, rng):
    if not isinstance(partial, _Partial):
        partial = _Partial(
            finished=tuple(),
            current=tuple(),
            remaining=tuple(sorted(int(c) for c in partial)),
        )

    routes = list(partial.finished)
    if partial.current:
        routes.append(partial.current)

    remaining = list(partial.remaining)
    rng.shuffle(remaining)

    for c in remaining:
        d = inst.demand[c]
        if routes:
            last = routes[-1]
            load = sum(inst.demand[i] for i in last)
            if load + d <= inst.capacity:
                routes[-1] = last + (c,)
                continue
        routes.append((c,))

    return canonical(tuple(routes))
