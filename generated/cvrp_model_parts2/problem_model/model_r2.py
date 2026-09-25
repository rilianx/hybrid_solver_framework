from __future__ import annotations

from random import Random
from math import hypot
from typing import Iterable, Sequence

from examples.cvrp.instance import CVRPInstance

COMPONENT = {
    "name": "cvrp_heuristic_view",
    "slot": "heuristic_view",
    "compatible_skeletons": [],
    "requires": [],
    "params": {
        "penalty": {"type": "float", "range": [1e3, 1e9]},
    },
}

PENALTY = 1e6


def _as_routes(sol) -> list[tuple[int, ...]]:
    if sol is None:
        return []
    return [tuple(route) for route in sol if route is not None and len(route) > 0]


def canonical(sol):
    routes = _as_routes(sol)
    routes.sort()
    return tuple(routes)


def trivial_solution(inst: CVRPInstance):
    return tuple((c,) for c in inst.customers)


def from_answer(inst: CVRPInstance, answer):
    routes = []
    seen = []
    for route in answer:
        rt = tuple(int(c) for c in route)
        routes.append(rt)
        seen.extend(rt)
    return canonical(routes)


def random_solution(inst: CVRPInstance, rng: Random):
    customers = list(inst.customers)
    rng.shuffle(customers)

    routes = []
    current = []
    load = 0.0
    cap = inst.capacity

    for c in customers:
        d = inst.demand[c]
        if current and load + d > cap:
            routes.append(tuple(current))
            current = [c]
            load = d
        else:
            current.append(c)
            load += d
    if current:
        routes.append(tuple(current))

    # Randomize route order without affecting feasibility
    rng.shuffle(routes)
    return canonical(routes)


def violations(inst: CVRPInstance, sol) -> dict[str, float]:
    routes = _as_routes(sol)
    counts = [0] * (inst.n_customers + 1)
    for route in routes:
        for c in route:
            if 1 <= c <= inst.n_customers:
                counts[c] += 1
            else:
                counts.append(1)

    visita = 0.0
    for c in inst.customers:
        visita += abs(counts[c] - 1)

    capacidad = 0.0
    for route in routes:
        load = sum(inst.demand[c] for c in route)
        if load > inst.capacity:
            capacidad += load - inst.capacity

    return {"visita": float(visita), "capacidad": float(capacidad)}


def cost_terms(inst: CVRPInstance, sol) -> dict[str, float]:
    routes = _as_routes(sol)
    dist = 0.0
    for route in routes:
        if not route:
            continue
        prev = 0
        for c in route:
            dist += inst.dist(prev, c)
            prev = c
        dist += inst.dist(prev, 0)

    viol = violations(inst, sol)
    penalty = PENALTY * (viol["visita"] + viol["capacidad"])
    return {"distancia": float(dist + penalty)}


# ---- vista MIP ----
from typing import Dict, List, Tuple

from examples.cvrp.instance import CVRPInstance


COMPONENT = {
    "name": "cvrp_mip_view",
    "slot": "mip_view",
    "compatible_skeletons": [],
    "requires": ["cvrp_heuristic_view"],
    "params": {},
}


def _x_name(i: int, j: int) -> str:
    return f"x_{i}_{j}"


def _u_name(i: int) -> str:
    return f"u_{i}"


def _pen_name() -> str:
    return "penalty_total"


def _routes_from_sol(sol) -> list[tuple[int, ...]]:
    if sol is None:
        return []
    routes: list[tuple[int, ...]] = []
    for route in sol:
        if route is None:
            continue
        rt = tuple(int(c) for c in route if c is not None)
        if rt:
            routes.append(rt)
    routes.sort()
    return routes


def _all_x_names(inst: CVRPInstance) -> list[str]:
    names: list[str] = []
    for i in range(inst.n_customers + 1):
        for j in range(inst.n_customers + 1):
            if i != j:
                names.append(_x_name(i, j))
    return names


def variables(inst: CVRPInstance) -> dict[str, tuple[float, float, str]]:
    vars_: dict[str, tuple[float, float, str]] = {}
    q = float(inst.capacity)

    for name in _all_x_names(inst):
        vars_[name] = (0.0, 1.0, "binary")

    for c in inst.customers:
        d = float(inst.demand[c])
        vars_[_u_name(c)] = (d, q, "continuous")

    # Auxiliary variable used only in the evaluated objective
    vars_[_pen_name()] = (0.0, 1e12, "continuous")
    return vars_


def structural_variables(inst: CVRPInstance) -> list[str]:
    return _all_x_names(inst)


def to_assignment(inst: CVRPInstance, sol) -> dict[str, float]:
    routes = _routes_from_sol(sol)
    x = {name: 0.0 for name in structural_variables(inst)}

    for route in routes:
        prev = 0
        for c in route:
            name = _x_name(prev, c)
            if name in x:
                x[name] = 1.0
            prev = c
        end_name = _x_name(prev, 0)
        if end_name in x:
            x[end_name] = 1.0

    return x


def aux_values(inst: CVRPInstance, sol) -> dict[str, float]:
    routes = _routes_from_sol(sol)
    vals: dict[str, float] = {}
    q = float(inst.capacity)

    # Load-like auxiliary values along each route, one value per customer.
    for c in inst.customers:
        vals[_u_name(c)] = float(inst.demand[c])

    # Penalty identical in spirit to the heuristic view: visit violations + capacity violations.
    counts = {c: 0 for c in inst.customers}
    cap_pen = 0.0

    for route in routes:
        load = 0.0
        for c in route:
            if c in counts:
                counts[c] += 1
            load += float(inst.demand[c])
            vals[_u_name(c)] = load
        if load > q:
            cap_pen += load - q

    visit_pen = 0.0
    for c in inst.customers:
        visit_pen += abs(counts[c] - 1)

    vals[_pen_name()] = 1e6 * (visit_pen + cap_pen)
    return vals


def from_assignment(inst: CVRPInstance, x) -> tuple[tuple[int, ...], ...]:
    n = inst.n_customers

    def val(i: int, j: int) -> float:
        return float(x.get(_x_name(i, j), 0.0))

    succ: dict[int, int] = {}
    pred: dict[int, int] = {}

    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            if val(i, j) > 0.5:
                succ[i] = j
                pred[j] = i

    routes: list[tuple[int, ...]] = []
    starts = [c for c in inst.customers if pred.get(c, 0) == 0]

    seen_global = set()
    for start in sorted(starts):
        if start in seen_global:
            continue
        route: list[int] = []
        cur = start
        seen_local = set()
        while cur != 0 and cur not in seen_local:
            seen_local.add(cur)
            seen_global.add(cur)
            route.append(cur)
            cur = succ.get(cur, 0)
        if route:
            routes.append(tuple(route))

    routes.sort()
    return tuple(routes)


def constraint_families(inst: CVRPInstance) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    fam: dict[str, list[tuple[dict[str, float], str, float]]] = {"visita": [], "capacidad": []}
    n = inst.n_customers
    q = float(inst.capacity)

    # Each customer has exactly one incoming and one outgoing arc.
    for j in inst.customers:
        in_coeffs = {_x_name(i, j): 1.0 for i in range(n + 1) if i != j}
        out_coeffs = {_x_name(j, k): 1.0 for k in range(n + 1) if k != j}
        fam["visita"].append((in_coeffs, "==", 1.0))
        fam["visita"].append((out_coeffs, "==", 1.0))

    # Load bounds for customer-load variables.
    for c in inst.customers:
        d = float(inst.demand[c])
        fam["capacidad"].append(({_u_name(c): 1.0}, ">=", d))
        fam["capacidad"].append(({_u_name(c): 1.0}, "<=", q))

    # Load propagation / subtour elimination:
    # u_i - u_j + q * x_ij <= q - d_j   for all i != j, i,j in customers
    # When x_ij = 1 => u_j >= u_i + d_j
    for i in inst.customers:
        for j in inst.customers:
            if i == j:
                continue
            coeffs = {
                _u_name(i): 1.0,
                _u_name(j): -1.0,
                _x_name(i, j): q,
            }
            fam["capacidad"].append((coeffs, "<=", q - float(inst.demand[j])))

    return fam


def objective_terms(inst: CVRPInstance) -> dict[str, tuple[dict[str, float], float]]:
    coeffs: dict[str, float] = {}
    for i in range(inst.n_customers + 1):
        for j in range(inst.n_customers + 1):
            if i != j:
                coeffs[_x_name(i, j)] = float(inst.dist(i, j))
    coeffs[_pen_name()] = 1.0
    return {"distancia": (coeffs, 0.0)}


def variable_groups(inst: CVRPInstance) -> dict[str, list[str]]:
    xs = structural_variables(inst)
    if not xs:
        return {"g1": []}

    # Two balanced blocks, each safely under 60% of the structural variables.
    mid = (len(xs) + 1) // 2
    return {
        "g1": xs[:mid],
        "g2": xs[mid:],
    }
