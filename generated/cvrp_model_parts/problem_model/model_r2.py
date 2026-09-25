from __future__ import annotations

from typing import Iterable
import math
import random

from examples.cvrp.instance import CVRPInstance


Solution = tuple[tuple[int, ...], ...]


PENALTY_VISIT = 1_000_000.0
PENALTY_CAPACITY = 1_000_000.0


def _normalize_route(route: Iterable[int]) -> tuple[int, ...]:
    return tuple(int(c) for c in route)


def canonical(sol) -> Solution:
    """
    Forma canónica: tupla de rutas, cada ruta una tupla de clientes.
    El orden de las rutas no importa; se ordenan lexicográficamente.
    """
    routes = [_normalize_route(route) for route in sol]
    routes = [route for route in routes if len(route) > 0]
    routes.sort()
    return tuple(routes)


def trivial_solution(inst: CVRPInstance) -> Solution:
    """Una solución factible simple: cada cliente en su propia ruta."""
    return tuple((c,) for c in inst.customers)


def random_solution(inst: CVRPInstance, rng: random.Random) -> Solution:
    """
    Construye una solución factible aleatoria:
    permuta clientes y los empaqueta vorazmente respetando capacidad.
    """
    customers = list(inst.customers)
    rng.shuffle(customers)

    routes = []
    current = []
    load = 0.0

    for c in customers:
        dc = inst.demand[c]
        if current and load + dc > inst.capacity:
            routes.append(tuple(current))
            current = [c]
            load = dc
        else:
            current.append(c)
            load += dc

    if current:
        routes.append(tuple(current))

    return canonical(routes)


def from_answer(inst: CVRPInstance, answer) -> Solution:
    """Convierte la respuesta en formato neutral a la representación canónica."""
    return canonical(answer)


def violations(inst: CVRPInstance, sol) -> dict[str, float]:
    """
    Magnitudes de violación:
    - visita: clientes faltantes + visitas extra
    - capacidad: suma de excesos de carga en rutas
    """
    sol = canonical(sol)
    n = inst.n_customers

    counts = [0] * (n + 1)
    for route in sol:
        for c in route:
            if 1 <= c <= n:
                counts[c] += 1
            else:
                # Cliente fuera de rango: lo tratamos como violación de visita.
                # Se cuenta aparte como una visita extra.
                pass

    missing = 0
    extra = 0
    for c in inst.customers:
        if counts[c] == 0:
            missing += 1
        elif counts[c] > 1:
            extra += counts[c] - 1

    visit_violation = float(missing + extra)

    cap_violation = 0.0
    for route in sol:
        load = sum(inst.demand[c] for c in route if 1 <= c <= n)
        if load > inst.capacity:
            cap_violation += load - inst.capacity

    return {"visita": visit_violation, "capacidad": float(cap_violation)}


def _route_distance(inst: CVRPInstance, route: tuple[int, ...]) -> float:
    if not route:
        return 0.0
    total = inst.dist(0, route[0])
    for a, b in zip(route, route[1:]):
        total += inst.dist(a, b)
    total += inst.dist(route[-1], 0)
    return total


def cost_terms(inst: CVRPInstance, sol) -> dict[str, float]:
    """
    Costo a minimizar desglosado por términos.
    El término 'distancia' incluye una penalización grande si la solución es infactible.
    """
    sol = canonical(sol)
    dist = sum(_route_distance(inst, route) for route in sol)
    vio = violations(inst, sol)
    penalty = PENALTY_VISIT * vio["visita"] + PENALTY_CAPACITY * vio["capacidad"]
    return {"distancia": float(dist + penalty)}


# ---- vista MIP ----
from typing import Dict, List, Tuple

from examples.cvrp.instance import CVRPInstance


COMPONENT = {
    "name": "cvrp_mip_view",
    "slot": "mip_view",
    "compatible_skeletons": [],
    "requires": ["canonical", "PENALTY_VISIT", "PENALTY_CAPACITY", "cost_terms", "violations"],
    "params": {},
}


def _arc_name(i: int, j: int) -> str:
    return f"x_{i}_{j}"


def _u_name(c: int) -> str:
    return f"u_{c}"


def variables(inst: CVRPInstance) -> dict[str, tuple[float, float, str]]:
    vars_: dict[str, tuple[float, float, str]] = {}
    nodes = range(0, inst.n_customers + 1)

    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            vars_[_arc_name(i, j)] = (0.0, 1.0, "binary")

    for c in inst.customers:
        vars_[_u_name(c)] = (float(inst.demand[c]), float(inst.capacity), "continuous")

    return vars_


def structural_variables(inst: CVRPInstance) -> list[str]:
    nodes = range(0, inst.n_customers + 1)
    return [_arc_name(i, j) for i in nodes for j in nodes if i != j]


def to_assignment(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)
    x: dict[str, float] = {name: 0.0 for name in structural_variables(inst)}

    for route in sol:
        if not route:
            continue
        x[_arc_name(0, route[0])] = 1.0
        for a, b in zip(route, route[1:]):
            x[_arc_name(a, b)] = 1.0
        x[_arc_name(route[-1], 0)] = 1.0

    return x


def aux_values(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)
    u: dict[str, float] = {}

    for route in sol:
        load = 0.0
        for c in route:
            load += float(inst.demand[c])
            u[_u_name(c)] = load

    for c in inst.customers:
        u.setdefault(_u_name(c), float(inst.demand[c]))

    return u


def from_assignment(inst: CVRPInstance, x) -> "sol":
    n = inst.n_customers

    succ = {i: None for i in range(n + 1)}
    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            if float(x.get(_arc_name(i, j), 0.0)) > 0.5:
                succ[i] = j
                break

    routes = []
    seen_customers = set()

    for j in range(1, n + 1):
        if float(x.get(_arc_name(0, j), 0.0)) <= 0.5 or j in seen_customers:
            continue

        route = []
        cur = j
        while cur is not None and cur != 0 and cur not in seen_customers:
            route.append(cur)
            seen_customers.add(cur)
            cur = succ[cur]
        if route:
            routes.append(tuple(route))

    return canonical(routes)


def constraint_families(inst: CVRPInstance) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    fam: dict[str, list[tuple[dict[str, float], str, float]]] = {"visita": [], "capacidad": []}
    n = inst.n_customers
    nodes = range(0, n + 1)
    Q = float(inst.capacity)

    for c in inst.customers:
        incoming = {_arc_name(i, c): 1.0 for i in nodes if i != c}
        outgoing = {_arc_name(c, j): 1.0 for j in nodes if j != c}
        fam["visita"].append((incoming, "==", 1.0))
        fam["visita"].append((outgoing, "==", 1.0))

    # Load variables: q_c <= u_c <= Q
    for c in inst.customers:
        q = float(inst.demand[c])
        fam["capacidad"].append(({_u_name(c): 1.0}, ">=", q))
        fam["capacidad"].append(({_u_name(c): 1.0}, "<=", Q))

    # Standard CVRP MTZ load propagation:
    # u_i - u_j + Q x_ij <= Q - q_j
    # If x_ij = 1, then u_j >= u_i + q_j
    # If x_ij = 0, the inequality is relaxed by the big-M term.
    for i in inst.customers:
        for j in inst.customers:
            if i == j:
                continue
            coeffs = {_u_name(i): 1.0, _u_name(j): -1.0, _arc_name(i, j): Q}
            rhs = Q - float(inst.demand[j])
            fam["capacidad"].append((coeffs, "<=", rhs))

    return fam


def objective_terms(inst: CVRPInstance) -> dict[str, tuple[dict[str, float], float]]:
    coeffs: dict[str, float] = {}
    n = inst.n_customers
    nodes = range(0, n + 1)
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            coeffs[_arc_name(i, j)] = float(inst.dist(i, j))
    return {"distancia": (coeffs, 0.0)}


def variable_groups(inst: CVRPInstance) -> dict[str, list[str]]:
    return {"arcos": structural_variables(inst)}
