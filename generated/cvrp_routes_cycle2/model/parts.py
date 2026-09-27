from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from random import Random
from typing import Any
from weakref import WeakKeyDictionary

from examples.cvrp.instance import CVRPInstance


# =============================================================================
# Caches por instancia
# =============================================================================

@dataclass(frozen=True)
class _InstData:
    n: int
    capacity: float
    customers: tuple[int, ...]
    demand: tuple[float, ...]
    dist: tuple[tuple[float, ...], ...]
    max_dist: float
    total_demand: float


_INST_CACHE: "WeakKeyDictionary[Any, _InstData]" = WeakKeyDictionary()


def _get_inst_data(inst: CVRPInstance) -> _InstData:
    try:
        return _INST_CACHE[inst]
    except Exception:
        n = int(inst.n_customers)
        customers = tuple(int(c) for c in inst.customers)
        demand = tuple(float(inst.demand[c]) for c in range(n + 1))
        dist = tuple(tuple(float(inst.dist(i, j)) for j in range(n + 1)) for i in range(n + 1))
        max_dist = max((dist[i][j] for i in range(n + 1) for j in range(n + 1)), default=1.0)
        total_demand = float(sum(demand[c] for c in customers))
        data = _InstData(
            n=n,
            capacity=float(inst.capacity),
            customers=customers,
            demand=demand,
            dist=dist,
            max_dist=float(max_dist),
            total_demand=total_demand,
        )
        try:
            _INST_CACHE[inst] = data
        except Exception:
            pass
        return data


# =============================================================================
# Utilidades comunes
# =============================================================================

def canonical(sol):
    routes = []
    for route in sol:
        if route:
            routes.append(tuple(int(c) for c in route))
    routes.sort(key=lambda r: r[0])
    return tuple(routes)


def _canonical_sol(sol):
    if isinstance(sol, tuple) and (not sol or isinstance(sol[0], tuple)):
        return canonical(sol)
    return canonical(tuple(sol))


# =============================================================================
# Evaluación
# =============================================================================

def trivial_solution(inst: CVRPInstance):
    data = _get_inst_data(inst)
    return tuple((c,) for c in data.customers)


def random_solution(inst: CVRPInstance, rng: Random):
    data = _get_inst_data(inst)
    customers = list(data.customers)
    rng.shuffle(customers)

    routes = []
    current = []
    current_load = 0.0
    cap = data.capacity
    demand = data.demand

    for c in customers:
        d = demand[c]
        if current and current_load + d > cap and rng.random() < 0.8:
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


@lru_cache(maxsize=8192)
def _violations_cached(inst_key: int, sol: tuple[tuple[int, ...], ...]) -> tuple[float, float]:
    inst = _INST_REF[inst_key]
    data = _get_inst_data(inst)
    n = data.n
    cap = data.capacity
    demand = data.demand

    counts = [0] * (n + 1)
    invalid = 0

    for route in sol:
        load = 0.0
        for c in route:
            if 1 <= c <= n:
                counts[c] += 1
                load += demand[c]
            else:
                invalid += 1
        # capacidad
        if load > cap:
            pass

    visita = float(invalid)
    for c in data.customers:
        visita += abs(counts[c] - 1)

    capacidad = 0.0
    for route in sol:
        load = 0.0
        for c in route:
            if 1 <= c <= n:
                load += demand[c]
        if load > cap:
            capacidad += load - cap

    return float(visita), float(capacidad)


# weak reference support for cached evaluation
_INST_REF: dict[int, CVRPInstance] = {}


def _inst_key(inst: CVRPInstance) -> int:
    k = id(inst)
    _INST_REF[k] = inst
    return k


def violations(inst: CVRPInstance, sol) -> dict[str, float]:
    s = _canonical_sol(sol)
    v, c = _violations_cached(_inst_key(inst), s)
    return {"visita": v, "capacidad": c}


@lru_cache(maxsize=8192)
def _cost_cached(inst_key: int, sol: tuple[tuple[int, ...], ...]) -> float:
    inst = _INST_REF[inst_key]
    data = _get_inst_data(inst)
    n = data.n
    dist = data.dist

    distance = 0.0
    for route in sol:
        prev = 0
        for c in route:
            if 1 <= c <= n:
                distance += dist[prev][c]
                prev = c
        distance += dist[prev][0]

    v1, v2 = _violations_cached(inst_key, sol)
    penalty_scale = 1.0 + 1000.0 * (n + 1) * data.max_dist
    return float(distance + penalty_scale * (v1 + v2))


def cost_terms(inst: CVRPInstance, sol) -> dict[str, float]:
    s = _canonical_sol(sol)
    return {"distancia": _cost_cached(_inst_key(inst), s)}


# =============================================================================
# Vista MIP
# =============================================================================

def _x_name(i: int, j: int) -> str:
    return f"x_{i}_{j}"


def _f_name(i: int, j: int) -> str:
    return f"f_{i}_{j}"


def variables(inst) -> dict[str, tuple[float, float, str]]:
    data = _get_inst_data(inst)
    n = data.n
    vars_: dict[str, tuple[float, float, str]] = {}

    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                vars_[_x_name(i, j)] = (0.0, 1.0, "binary")
                vars_[_f_name(i, j)] = (0.0, float(data.capacity), "continuous")

    return vars_


def structural_variables(inst) -> list[str]:
    data = _get_inst_data(inst)
    n = data.n
    return [_x_name(i, j) for i in range(n + 1) for j in range(n + 1) if i != j]


@lru_cache(maxsize=8192)
def _structural_variables_cached(inst_key: int) -> tuple[str, ...]:
    inst = _INST_REF[inst_key]
    return tuple(structural_variables(inst))


def to_assignment(inst, sol) -> dict[str, float]:
    s = _canonical_sol(sol)
    data = _get_inst_data(inst)
    n = data.n

    x = {_x_name(i, j): 0.0 for i in range(n + 1) for j in range(n + 1) if i != j}

    for route in s:
        prev = 0
        for c in route:
            if 1 <= c <= n:
                x[_x_name(prev, c)] = 1.0
                prev = c
        x[_x_name(prev, 0)] = 1.0

    return x


def aux_values(inst, sol) -> dict[str, float]:
    s = _canonical_sol(sol)
    data = _get_inst_data(inst)
    n = data.n
    demand = data.demand

    f = {_f_name(i, j): 0.0 for i in range(n + 1) for j in range(n + 1) if i != j}

    for route in s:
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
    data = _get_inst_data(inst)
    n = data.n

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
    data = _get_inst_data(inst)
    n = data.n
    q = float(data.capacity)
    total_demand = data.total_demand

    fam: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "visita": [],
        "capacidad": [],
    }

    for c in data.customers:
        in_coefs = {_x_name(i, c): 1.0 for i in range(n + 1) if i != c}
        out_coefs = {_x_name(c, j): 1.0 for j in range(n + 1) if j != c}
        fam["visita"].append((in_coefs, "==", 1.0))
        fam["visita"].append((out_coefs, "==", 1.0))

    for j in data.customers:
        coefs: dict[str, float] = {}
        for i in range(n + 1):
            if i != j:
                name = _f_name(i, j)
                coefs[name] = coefs.get(name, 0.0) + 1.0
        for k in range(n + 1):
            if k != j:
                name = _f_name(j, k)
                coefs[name] = coefs.get(name, 0.0) - 1.0
        fam["capacidad"].append((coefs, "==", float(data.demand[j])))

    depot_coefs: dict[str, float] = {}
    for k in range(1, n + 1):
        name = _f_name(0, k)
        depot_coefs[name] = depot_coefs.get(name, 0.0) + 1.0
        name = _f_name(k, 0)
        depot_coefs[name] = depot_coefs.get(name, 0.0) - 1.0
    fam["capacidad"].append((depot_coefs, "==", total_demand))

    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                fam["capacidad"].append(({_f_name(i, j): 1.0, _x_name(i, j): -q}, "<=", 0.0))

    return fam


def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]:
    data = _get_inst_data(inst)
    n = data.n
    coefs: dict[str, float] = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                coefs[_x_name(i, j)] = data.dist[i][j]
    return {"distancia": (coefs, 0.0)}


def variable_groups(inst) -> dict[str, list[str]]:
    key = _inst_key(inst)
    xs = _structural_variables_cached(key)
    groups: dict[str, list[str]] = defaultdict(list)

    for idx, name in enumerate(xs):
        groups[f"g{idx % 4}"].append(name)

    for k in range(4):
        groups.setdefault(f"g{k}", [])

    return dict(groups)


# =============================================================================
# Vista constructiva
# =============================================================================

@dataclass(frozen=True)
class _Partial:
    finished: tuple[tuple[int, ...], ...]
    current: tuple[int, ...]
    remaining: tuple[int, ...]


def empty_partial(inst):
    data = _get_inst_data(inst)
    return _Partial(finished=tuple(), current=tuple(), remaining=tuple(data.customers))


def candidates(inst, partial) -> list:
    if not isinstance(partial, _Partial):
        partial = _Partial(
            finished=tuple(),
            current=tuple(),
            remaining=tuple(sorted(int(c) for c in partial)),
        )
    return list(partial.remaining)


def apply_action(inst, partial, action):
    data = _get_inst_data(inst)
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
        load = sum(data.demand[i] for i in partial.current)
        if load + data.demand[c] <= data.capacity:
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
    data = _get_inst_data(inst)
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
        d = data.demand[c]
        if routes:
            last = routes[-1]
            load = sum(data.demand[i] for i in last)
            if load + d <= data.capacity:
                routes[-1] = last + (c,)
                continue
        routes.append((c,))

    return canonical(tuple(routes))
