from __future__ import annotations

from random import Random
from typing import Iterable

from examples.cvrp.instance import CVRPInstance


def canonical(sol):
    """
    Forma canónica: tupla de rutas no vacías, cada ruta como tupla de enteros,
    ordenadas por su primer cliente.
    """
    if sol is None:
        return tuple()
    routes = []
    for route in sol:
        rt = tuple(int(c) for c in route if c is not None)
        if len(rt) > 0:
            routes.append(rt)
    routes.sort(key=lambda r: r[0])
    return tuple(routes)


def trivial_solution(inst):
    """Solución factible: una ruta por cliente."""
    return tuple((c,) for c in inst.customers)


def random_solution(inst, rng):
    """Solución aleatoria con estructura válida: partición aleatoria de clientes en rutas."""
    customers = list(inst.customers)
    rng.shuffle(customers)

    routes = []
    current = []
    load = 0.0

    for c in customers:
        d = inst.demand[c]
        # iniciar nueva ruta si se excedería capacidad con cierta probabilidad,
        # o si la ruta actual ya tiene suficientes clientes.
        if current and (load + d > inst.capacity or rng.random() < 0.22):
            routes.append(tuple(current))
            current = []
            load = 0.0
        current.append(c)
        load += d

    if current:
        routes.append(tuple(current))

    return canonical(routes)


def from_answer(inst, answer):
    """Convierte la respuesta en formato neutral a la representación canónica."""
    return canonical(answer)


def _routes_of(sol) -> list[tuple[int, ...]]:
    return [tuple(route) for route in canonical(sol)]


def violations(inst, sol) -> dict[str, float]:
    routes = _routes_of(sol)

    counts = [0] * (inst.n_customers + 1)
    for route in routes:
        for c in route:
            if 1 <= c <= inst.n_customers:
                counts[c] += 1
            else:
                # Cliente fuera de rango: cuenta como visita extra "fantasma"
                # para mantener una penalización finita.
                pass

    visita = 0.0
    for c in inst.customers:
        visita += abs(counts[c] - 1)

    capacidad = 0.0
    for route in routes:
        load = sum(inst.demand[c] for c in route if 1 <= c <= inst.n_customers)
        if load > inst.capacity:
            capacidad += load - inst.capacity

    return {"visita": float(visita), "capacidad": float(capacidad)}


def cost_terms(inst, sol) -> dict[str, float]:
    routes = _routes_of(sol)

    distance = 0.0
    for route in routes:
        if not route:
            continue
        prev = 0
        for c in route:
            if 1 <= c <= inst.n_customers:
                distance += inst.dist(prev, c)
                prev = c
        distance += inst.dist(prev, 0)

    v = violations(inst, sol)

    # Cota superior simple para cualquier solución factible:
    # 2 * sum dist(0, c) (visitar cada cliente por separado).
    feasible_upper = 0.0
    for c in inst.customers:
        feasible_upper += 2.0 * inst.dist(0, c)

    big_m = feasible_upper + 1.0
    penalty = big_m if (v["visita"] > 0.0 or v["capacidad"] > 0.0) else 0.0

    return {"distancia": float(distance + penalty)}


# ---- vista MIP ----
from typing import Dict

from examples.cvrp.instance import CVRPInstance


def _x_name(i: int, j: int) -> str:
    return f"x[{i},{j}]"


def _u_name(c: int) -> str:
    return f"u[{c}]"


def _routes_from_sol(sol):
    if sol is None:
        return tuple()
    routes = []
    for route in sol:
        rt = tuple(int(c) for c in route if c is not None)
        if rt:
            routes.append(rt)
    routes.sort(key=lambda r: r[0])
    return tuple(routes)


def variables(inst) -> dict[str, tuple[float, float, str]]:
    vars_: dict[str, tuple[float, float, str]] = {}
    n = inst.n_customers

    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                vars_[_x_name(i, j)] = (0.0, 1.0, "binary")

    for c in inst.customers:
        vars_[_u_name(c)] = (float(inst.demand[c]), float(inst.capacity), "continuous")

    return vars_


def structural_variables(inst) -> list[str]:
    n = inst.n_customers
    return [_x_name(i, j) for i in range(n + 1) for j in range(n + 1) if i != j]


def to_assignment(inst, sol) -> dict[str, float]:
    n = inst.n_customers
    x = {name: 0.0 for name in structural_variables(inst)}

    for route in _routes_from_sol(sol):
        prev = 0
        for c in route:
            if 1 <= c <= n:
                x[_x_name(prev, c)] = 1.0
                prev = c
        x[_x_name(prev, 0)] = 1.0

    return x


def from_assignment(inst, x) -> "sol":
    n = inst.n_customers

    succ: Dict[int, int] = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j and float(x.get(_x_name(i, j), 0.0)) > 0.5:
                succ[i] = j
                break

    routes = []
    used = set()

    for start in range(1, n + 1):
        if float(x.get(_x_name(0, start), 0.0)) <= 0.5:
            continue
        cur = start
        route = []
        seen = set()
        while 1 <= cur <= n and cur not in seen:
            seen.add(cur)
            used.add(cur)
            route.append(cur)
            cur = succ.get(cur, 0)
            if cur == 0:
                break
        if route:
            routes.append(tuple(route))

    for c in range(1, n + 1):
        if c not in used:
            routes.append((c,))

    return tuple(sorted(routes, key=lambda r: r[0]))


def aux_values(inst, sol) -> dict[str, float]:
    routes = _routes_from_sol(sol)
    vals: dict[str, float] = {}

    for c in inst.customers:
        vals[_u_name(c)] = float(inst.demand[c])

    for route in routes:
        load = 0.0
        for c in route:
            if 1 <= c <= inst.n_customers:
                load += float(inst.demand[c])
                vals[_u_name(c)] = load

    return vals


def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    fams: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "visita.entrada": [],
        "visita.salida": [],
        "capacidad.cota_inf": [],
        "capacidad.cota_sup": [],
        "capacidad.transicion": [],
    }

    n = inst.n_customers
    q = float(inst.capacity)

    for c in inst.customers:
        coef_in: dict[str, float] = {}
        coef_out: dict[str, float] = {}
        for i in range(n + 1):
            if i != c:
                coef_in[_x_name(i, c)] = 1.0
                coef_out[_x_name(c, i)] = 1.0
        fams["visita.entrada"].append((coef_in, "==", 1.0))
        fams["visita.salida"].append((coef_out, "==", 1.0))

    for c in inst.customers:
        fams["capacidad.cota_inf"].append(({_u_name(c): 1.0}, ">=", float(inst.demand[c])))
        fams["capacidad.cota_sup"].append(({_u_name(c): 1.0}, "<=", q))

    for i in inst.customers:
        for j in inst.customers:
            if i == j:
                continue
            coef = {_u_name(i): 1.0, _u_name(j): -1.0, _x_name(i, j): q}
            fams["capacidad.transicion"].append((coef, "<=", q - float(inst.demand[j])))

    return fams


def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]:
    coef: dict[str, float] = {}
    n = inst.n_customers

    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                coef[_x_name(i, j)] = float(inst.dist(i, j))

    return {"distancia": (coef, 0.0)}


def variable_groups(inst) -> dict[str, list[str]]:
    n = inst.n_customers
    groups: dict[str, list[str]] = {f"g{k}": [] for k in range(4)}

    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            if i == 0 and j >= 1:
                gid = (j - 1) % 4
            elif i >= 1:
                gid = (i - 1) % 4
            else:
                gid = 0
            groups[f"g{gid}"].append(_x_name(i, j))

    return groups
