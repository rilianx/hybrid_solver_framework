from __future__ import annotations

from typing import Any
import random

from examples.cvrp.instance import CVRPInstance


COMPONENT = {
    "name": "cvrp_heuristic_view",
    "slot": "heuristic_view",
    "compatible_skeletons": ["generic"],
    "requires": ["problem_model"],
    "params": {},
}


def _normalize_route(route: Any) -> tuple[int, ...]:
    return tuple(int(c) for c in route)


def _normalize_solution(sol: Any) -> tuple[tuple[int, ...], ...]:
    routes = []
    for route in sol:
        r = _normalize_route(route)
        if r:
            routes.append(r)
    routes.sort()
    return tuple(routes)


def canonical(sol):
    return _normalize_solution(sol)


def trivial_solution(inst: CVRPInstance):
    routes = tuple((c,) for c in inst.customers)
    return canonical(routes)


def random_solution(inst: CVRPInstance, rng: random.Random):
    customers = list(inst.customers)
    rng.shuffle(customers)

    routes = []
    route = []
    load = 0.0

    for c in customers:
        d = inst.demand[c]
        if route and load + d > inst.capacity:
            routes.append(tuple(route))
            route = [c]
            load = d
        else:
            route.append(c)
            load += d

        if route and rng.random() < 0.25:
            routes.append(tuple(route))
            route = []
            load = 0.0

    if route:
        routes.append(tuple(route))

    if not routes:
        routes = [(c,) for c in customers]

    return canonical(routes)


def from_answer(inst: CVRPInstance, answer):
    return canonical(answer)


def violations(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)

    counts = {c: 0 for c in inst.customers}
    cap_excess = 0.0

    for route in sol:
        load = 0.0
        for c in route:
            if c in counts:
                counts[c] += 1
                load += inst.demand[c]
        cap_excess += max(0.0, load - inst.capacity)

    visita = sum(abs(count - 1) for count in counts.values())
    return {"visita": float(visita), "capacidad": float(cap_excess)}


def cost_terms(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)
    dist = 0.0

    for route in sol:
        prev = 0
        for c in route:
            dist += inst.dist(prev, c)
            prev = c
        dist += inst.dist(prev, 0)

    return {"distancia": float(dist)}


# ---- vista MIP ----
from typing import Any
import math

from examples.cvrp.instance import CVRPInstance


COMPONENT = {
    "name": "cvrp_mip_view",
    "slot": "mip_view",
    "compatible_skeletons": ["generic"],
    "requires": ["problem_model"],
    "params": {},
}


def _nodes(inst: CVRPInstance) -> range:
    return range(inst.n_customers + 1)


def _x(i: int, j: int) -> str:
    return f"x_{i}_{j}"


def _u(i: int) -> str:
    return f"u_{i}"


def variables(inst):
    n = inst.n_customers
    vars_: dict[str, tuple[float, float, str]] = {}

    # Arcos dirigidos entre nodos distintos
    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            vars_[_x(i, j)] = (0.0, 1.0, "binary")

    # Cargas acumuladas al llegar a cada cliente
    for i in range(1, n + 1):
        vars_[_u(i)] = (float(inst.demand[i]), float(inst.capacity), "continuous")

    return vars_


def structural_variables(inst):
    n = inst.n_customers
    return [_x(i, j) for i in range(n + 1) for j in range(n + 1) if i != j]


def aux_values(inst, sol):
    sol = canonical(sol)
    vals: dict[str, float] = {}

    for route in sol:
        load = 0.0
        for c in route:
            load += float(inst.demand[c])
            vals[_u(c)] = load

    for c in inst.customers:
        vals.setdefault(_u(c), float(inst.demand[c]))

    return vals


def to_assignment(inst, sol):
    sol = canonical(sol)
    x: dict[str, float] = {name: 0.0 for name in structural_variables(inst)}

    for route in sol:
        prev = 0
        for c in route:
            x[_x(prev, c)] = 1.0
            prev = c
        x[_x(prev, 0)] = 1.0

    return x


def from_assignment(inst, x):
    n = inst.n_customers
    succ: dict[int, int] = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            if float(x.get(_x(i, j), 0.0)) > 0.5:
                succ[i] = j

    routes = []
    seen = set()
    for first in range(1, n + 1):
        if float(x.get(_x(0, first), 0.0)) <= 0.5:
            continue
        route = []
        cur = first
        while cur != 0 and cur not in seen:
            seen.add(cur)
            route.append(cur)
            cur = succ.get(cur, 0)
        if route:
            routes.append(tuple(route))

    return canonical(routes)


def constraint_families(inst):
    n = inst.n_customers
    fam: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "visita": [],
        "capacidad": [],
    }

    # Cada cliente exactamente una vez: una entrada y una salida
    for c in inst.customers:
        in_coeffs = {_x(i, c): 1.0 for i in range(n + 1) if i != c}
        out_coeffs = {_x(c, j): 1.0 for j in range(n + 1) if j != c}
        fam["visita"].append((in_coeffs, "==", 1.0))
        fam["visita"].append((out_coeffs, "==", 1.0))

    # Variables de carga: q_j >= d_j
    for j in inst.customers:
        fam["capacidad"].append(({_u(j): 1.0}, ">=", float(inst.demand[j])))

    # MTZ-capacity:
    # u_j - u_i >= d_j - Q*(1-x_ij)  para i,j clientes, i!=j
    Q = float(inst.capacity)
    for i in inst.customers:
        for j in inst.customers:
            if i == j:
                continue
            coeffs = {_u(j): 1.0, _u(i): -1.0, _x(i, j): -Q}
            rhs = float(inst.demand[j] - Q)
            fam["capacidad"].append((coeffs, ">=", rhs))

    # Arco desde depósito: u_j >= d_j - Q*(1-x_0j)
    for j in inst.customers:
        fam["capacidad"].append(({_u(j): 1.0, _x(0, j): -Q}, ">=", float(inst.demand[j] - Q)))

    return fam


def objective_terms(inst):
    n = inst.n_customers
    coeffs = {_x(i, j): float(inst.dist(i, j)) for i in range(n + 1) for j in range(n + 1) if i != j}
    return {"distancia": (coeffs, 0.0)}


def variable_groups(inst):
    # Partición en varios grupos pequeños para Relax-and-Fix / Fix-and-Optimize.
    groups: dict[str, list[str]] = {}
    n = inst.n_customers

    # Agrupamos por origen, repartiendo en 4 bloques como mínimo.
    bucket_count = max(4, min(n + 1, 8))
    for b in range(bucket_count):
        groups[f"g{b}"] = []

    idx = 0
    for i in range(n + 1):
        bucket = idx % bucket_count
        for j in range(n + 1):
            if i == j:
                continue
            groups[f"g{bucket}"].append(_x(i, j))
        idx += 1

    return groups
