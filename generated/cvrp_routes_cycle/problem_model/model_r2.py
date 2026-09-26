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
from typing import Dict, List, Tuple


def _var_x(i: int, j: int) -> str:
    return f"x[{i},{j}]"


def _var_u(c: int) -> str:
    return f"u[{c}]"


def _var_pen() -> str:
    return "pen"


def canonical(sol):
    if sol is None:
        return tuple()
    routes = []
    for route in sol:
        rt = tuple(int(c) for c in route if c is not None)
        if len(rt) > 0:
            routes.append(rt)
    routes.sort(key=lambda r: r[0])
    return tuple(routes)


def violations(inst, sol) -> dict[str, float]:
    routes = canonical(sol)

    counts = [0] * (inst.n_customers + 1)
    for route in routes:
        for c in route:
            if 1 <= c <= inst.n_customers:
                counts[c] += 1

    visita = 0.0
    for c in inst.customers:
        visita += abs(counts[c] - 1)

    capacidad = 0.0
    for route in routes:
        load = sum(inst.demand[c] for c in route if 1 <= c <= inst.n_customers)
        if load > inst.capacity:
            capacidad += load - inst.capacity

    return {"visita": float(visita), "capacidad": float(capacidad)}


def _all_x_names(inst) -> list[str]:
    names = []
    n = inst.n_customers
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                names.append(_var_x(i, j))
    return names


def _all_u_names(inst) -> list[str]:
    return [_var_u(c) for c in inst.customers]


def variables(inst) -> dict[str, tuple[float, float, str]]:
    vars_: dict[str, tuple[float, float, str]] = {}
    n = inst.n_customers

    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                vars_[_var_x(i, j)] = (0.0, 1.0, "binary")

    for c in inst.customers:
        vars_[_var_u(c)] = (float(inst.demand[c]), float(inst.capacity), "continuous")

    vars_[_var_pen()] = (0.0, 1.0, "continuous")
    return vars_


def structural_variables(inst) -> list[str]:
    return _all_x_names(inst) + _all_u_names(inst)


def aux_values(inst, sol) -> dict[str, float]:
    routes = canonical(sol)
    vals: dict[str, float] = {_var_pen(): 0.0}

    for route in routes:
        load = 0.0
        for c in route:
            if 1 <= c <= inst.n_customers:
                load += float(inst.demand[c])
                vals[_var_u(c)] = load

    for c in inst.customers:
        vals.setdefault(_var_u(c), float(inst.demand[c]))

    v = violations(inst, sol)
    vals[_var_pen()] = 1.0 if (v["visita"] > 0.0 or v["capacidad"] > 0.0) else 0.0
    return vals


def to_assignment(inst, sol) -> dict[str, float]:
    routes = canonical(sol)
    x: dict[str, float] = {}

    for name in structural_variables(inst):
        x[name] = 0.0

    for route in routes:
        prev = 0
        for c in route:
            if 1 <= c <= inst.n_customers:
                x[_var_x(prev, c)] = 1.0
                prev = c
        x[_var_x(prev, 0)] = 1.0

    return x


def from_assignment(inst, x) -> "sol":
    n = inst.n_customers

    succ = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i != j and float(x.get(_var_x(i, j), 0.0)) > 0.5:
                succ[i] = j
                break

    routes = []
    visited = set()

    for start in range(1, n + 1):
        if float(x.get(_var_x(0, start), 0.0)) <= 0.5:
            continue
        route = []
        cur = start
        seen = set()
        while 1 <= cur <= n and cur not in seen:
            seen.add(cur)
            visited.add(cur)
            route.append(cur)
            cur = succ.get(cur, 0)
            if cur == 0:
                break
        if route:
            routes.append(tuple(route))

    for c in range(1, n + 1):
        if c not in visited:
            routes.append((c,))

    return canonical(routes)


def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    fams: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "visita.entrada": [],
        "visita.salida": [],
        "capacidad.cota_inf": [],
        "capacidad.cota_sup": [],
        "capacidad.transicion": [],
    }

    n = inst.n_customers

    for c in inst.customers:
        coef_in = {}
        coef_out = {}
        for i in range(n + 1):
            if i != c:
                coef_in[_var_x(i, c)] = 1.0
                coef_out[_var_x(c, i)] = 1.0
        fams["visita.entrada"].append((coef_in, "==", 1.0))
        fams["visita.salida"].append((coef_out, "==", 1.0))

    for c in inst.customers:
        fams["capacidad.cota_inf"].append(({_var_u(c): 1.0}, ">=", float(inst.demand[c])))
        fams["capacidad.cota_sup"].append(({_var_u(c): 1.0}, "<=", float(inst.capacity)))

    Q = float(inst.capacity)
    for i in inst.customers:
        for j in inst.customers:
            if i == j:
                continue
            coef = {_var_u(j): 1.0, _var_u(i): -1.0, _var_x(i, j): Q}
            fams["capacidad.transicion"].append((coef, ">=", float(inst.demand[j])))

    return fams


def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]:
    coef: dict[str, float] = {}
    n = inst.n_customers

    for i in range(n + 1):
        for j in range(n + 1):
            if i != j:
                coef[_var_x(i, j)] = float(inst.dist(i, j))

    feasible_upper = 0.0
    for c in inst.customers:
        feasible_upper += 2.0 * float(inst.dist(0, c))
    big_m = feasible_upper + 1.0
    coef[_var_pen()] = big_m

    return {"distancia": (coef, 0.0)}


def variable_groups(inst) -> dict[str, list[str]]:
    n = inst.n_customers
    if n == 0:
        return {}

    groups: dict[str, list[str]] = {}

    # Partition structural variables only; never include auxiliary variables like pen.
    # Use four balanced blocks based on tail index / customer index.
    for g in range(4):
        groups[f"g{g}"] = []

    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            if i == 0:
                gid = j % 4
            else:
                gid = (i - 1) % 4
            groups[f"g{gid}"].append(_var_x(i, j))

    for idx, c in enumerate(inst.customers):
        groups[f"g{idx % 4}"].append(_var_u(c))

    # Remove empty groups to keep the output compact while preserving partitioning.
    return {k: v for k, v in groups.items() if v}
