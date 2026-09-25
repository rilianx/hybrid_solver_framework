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


def _nodes(inst: CVRPInstance) -> range:
    return range(0, inst.n_customers + 1)


def _x_name(i: int, j: int) -> str:
    return f"x_{i}_{j}"


def _u_name(i: int) -> str:
    return f"u_{i}"


def _pen_name() -> str:
    return "penalty_total"


def variables(inst: CVRPInstance) -> dict[str, tuple[float, float, str]]:
    vars_: dict[str, tuple[float, float, str]] = {}
    n = inst.n_customers
    q = float(inst.capacity)

    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            vars_[_x_name(i, j)] = (0.0, 1.0, "binary")

    for c in inst.customers:
        d = float(inst.demand[c])
        vars_[_u_name(c)] = (d, q, "continuous")

    vars_[_pen_name()] = (0.0, 1e12, "continuous")
    return vars_


def structural_variables(inst: CVRPInstance) -> list[str]:
    names: list[str] = []
    for i in range(inst.n_customers + 1):
        for j in range(inst.n_customers + 1):
            if i != j:
                names.append(_x_name(i, j))
    return names


def to_assignment(inst: CVRPInstance, sol) -> dict[str, float]:
    from examples.cvrp import heuristic_view as hv  # type: ignore

    routes = hv.canonical(sol)
    x: dict[str, float] = {_x_name(i, j): 0.0 for i in range(inst.n_customers + 1) for j in range(inst.n_customers + 1) if i != j}

    for route in routes:
        prev = 0
        for c in route:
            x[_x_name(prev, c)] = 1.0
            prev = c
        x[_x_name(prev, 0)] = 1.0

    return x


def aux_values(inst: CVRPInstance, sol) -> dict[str, float]:
    from examples.cvrp import heuristic_view as hv  # type: ignore

    routes = hv._as_routes(sol)
    u: dict[str, float] = {_u_name(c): float(inst.demand[c]) for c in inst.customers}

    total_pen = 0.0
    counts = [0] * (inst.n_customers + 1)
    for route in routes:
        load = 0.0
        for c in route:
            counts[c] += 1
            load += float(inst.demand[c])
            u[_u_name(c)] = load
        if load > float(inst.capacity):
            total_pen += load - float(inst.capacity)

    for c in inst.customers:
        total_pen += abs(counts[c] - 1.0)

    u[_pen_name()] = float(1e6 * total_pen)
    return u


def from_assignment(inst: CVRPInstance, x) -> tuple[tuple[int, ...], ...]:
    n = inst.n_customers
    succ: dict[int, int] = {}
    pred: dict[int, int] = {}

    def val(i: int, j: int) -> float:
        return float(x.get(_x_name(i, j), 0.0))

    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            if val(i, j) > 0.5:
                succ[i] = j
                pred[j] = i

    routes: list[tuple[int, ...]] = []
    starts = [j for j in inst.customers if pred.get(j, None) == 0]
    for start in starts:
        route: list[int] = []
        cur = start
        seen = set()
        while cur != 0 and cur not in seen:
            seen.add(cur)
            route.append(cur)
            cur = succ.get(cur, 0)
        if route:
            routes.append(tuple(route))

    return tuple(sorted(routes))


def constraint_families(inst: CVRPInstance) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    fam: dict[str, list[tuple[dict[str, float], str, float]]] = {"visita": [], "capacidad": []}
    n = inst.n_customers
    q = float(inst.capacity)

    for j in inst.customers:
        coeffs_in = {_x_name(i, j): 1.0 for i in range(n + 1) if i != j}
        coeffs_out = {_x_name(j, k): 1.0 for k in range(n + 1) if k != j}
        fam["visita"].append((coeffs_in, "==", 1.0))
        fam["visita"].append((coeffs_out, "==", 1.0))

    for c in inst.customers:
        fam["capacidad"].append(({_u_name(c): 1.0}, ">=", float(inst.demand[c])))
        fam["capacidad"].append(({_u_name(c): 1.0}, "<=", q))

    for i in inst.customers:
        for j in inst.customers:
            if i == j:
                continue
            coeffs = {
                _u_name(i): 1.0,
                _u_name(j): -1.0,
                _x_name(i, j): q,
            }
            rhs = q - float(inst.demand[j])
            fam["capacidad"].append((coeffs, "<=", rhs))

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
    n = len(xs)
    cut1 = max(1, n // 3)
    cut2 = max(cut1 + 1, (2 * n) // 3)
    return {
        "g1": xs[:cut1],
        "g2": xs[cut1:cut2],
        "g3": xs[cut2:],
    }
