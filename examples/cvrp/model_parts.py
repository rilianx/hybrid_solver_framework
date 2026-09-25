"""El modelo del CVRP escrito como piezas (`core.model_parts`): la referencia contra la que se
prueba el mecanismo y con la que se generan los casos de prueba (`cases.py`).

Formato neutral de respuesta (el de los casos): lista de rutas, cada una una lista de clientes
en orden de visita, sin el depósito. Familias: `visita` (cada cliente exactamente una vez) y
`capacidad` (carga de cada ruta <= Q). Términos del objetivo: `distancia`.

MIP: arcos binarios `x_i_j` (estructurales) y cargas `u_i` continuas (auxiliares); familias
`visita.entrada`, `visita.salida`, `visita.flota` (tantas salidas del depósito como entradas),
`capacidad.mtz` (u_j >= u_i + d_j - Q(1 - x_ij)) y `capacidad.carga` (d_i <= u_i <= Q).
"""

from __future__ import annotations

import math
from random import Random

from .instance import CVRPInstance


def canonical(sol):
    return tuple(sorted((tuple(r) for r in sol if r), key=lambda r: r[0]))


def trivial_solution(inst: CVRPInstance):
    return canonical([(c,) for c in inst.customers])


def random_solution(inst: CVRPInstance, rng: Random):
    custs = list(inst.customers)
    rng.shuffle(custs)
    routes, cur, load = [], [], 0.0
    for c in custs:
        if cur and (load + inst.demand[c] > inst.capacity or rng.random() < 0.25):
            routes.append(cur)
            cur, load = [], 0.0
        cur.append(c)
        load += inst.demand[c]
    routes.append(cur)
    return canonical(routes)


def from_answer(inst: CVRPInstance, answer):
    return canonical(tuple(int(c) for c in r) for r in answer)


def violations(inst: CVRPInstance, sol) -> dict[str, float]:
    seen: dict[int, int] = {}
    for r in sol:
        for c in r:
            seen[c] = seen.get(c, 0) + 1
    visit = sum(abs(seen.get(c, 0) - 1) for c in inst.customers) + sum(k for c, k in seen.items() if c not in inst.customers)
    cap = sum(max(0.0, sum(inst.demand[c] for c in r) - inst.capacity) for r in sol)
    return {"visita": float(visit), "capacidad": float(cap)}


def cost_terms(inst: CVRPInstance, sol) -> dict[str, float]:
    total = 0.0
    for r in sol:
        nodes = (0, *r, 0)
        total += sum(inst.dist(a, b) for a, b in zip(nodes, nodes[1:]))
    return {"distancia": total}


# ---------------------------------------------------------------- vista MIP
def _x(i, j):
    return f"x_{i}_{j}"


def _u(i):
    return f"u_{i}"


def structural_variables(inst: CVRPInstance):
    V = range(len(inst.coords))
    return [_x(i, j) for i in V for j in V if i != j]


def variables(inst: CVRPInstance):
    out = {v: (0.0, 1.0, "binary") for v in structural_variables(inst)}
    out.update({_u(i): (0.0, float(inst.capacity) * 2 + sum(inst.demand), "continuous") for i in inst.customers})
    return out


def to_assignment(inst: CVRPInstance, sol):
    x = {v: 0.0 for v in structural_variables(inst)}
    for r in sol:
        nodes = (0, *r, 0)
        for a, b in zip(nodes, nodes[1:]):
            if a != b:
                x[_x(a, b)] = 1.0
    return x


def aux_values(inst: CVRPInstance, sol):
    """Carga acumulada al llegar a cada cliente (la primera visita, si se repite)."""
    u = {_u(c): float(inst.demand[c]) for c in inst.customers}
    done = set()
    for r in sol:
        load = 0.0
        for c in r:
            load += inst.demand[c]
            if c not in done and c in inst.customers:
                u[_u(c)] = load
                done.add(c)
    return u


def from_assignment(inst: CVRPInstance, x):
    succ: dict[int, list[int]] = {}
    for name, v in x.items():
        if v is not None and round(v) >= 1:
            _, a, b = name.split("_")
            succ.setdefault(int(a), []).append(int(b))
    routes = []
    for first in sorted(succ.get(0, [])):
        route, cur, guard = [], first, 0
        while cur != 0 and guard <= inst.n_customers:
            route.append(cur)
            cur = succ.get(cur, [0])[0]
            guard += 1
        routes.append(tuple(route))
    return canonical(routes)


def constraint_families(inst: CVRPInstance):
    V = range(len(inst.coords))
    C = list(inst.customers)
    Q = float(inst.capacity)
    fams = {
        "visita.entrada": [({_x(j, i): 1.0 for j in V if j != i}, "==", 1.0) for i in C],
        "visita.salida": [({_x(i, j): 1.0 for j in V if j != i}, "==", 1.0) for i in C],
        "visita.flota": [({**{_x(0, j): 1.0 for j in C}, **{_x(j, 0): -1.0 for j in C}}, "==", 0.0)],
        "capacidad.mtz": [({_u(j): 1.0, _u(i): -1.0, _x(i, j): -Q}, ">=", inst.demand[j] - Q)
                          for i in C for j in C if i != j],
        "capacidad.carga": [({_u(i): 1.0}, "<=", Q) for i in C] + [({_u(i): 1.0}, ">=", float(inst.demand[i])) for i in C],
    }
    return fams


def objective_terms(inst: CVRPInstance):
    V = range(len(inst.coords))
    return {"distancia": ({_x(i, j): inst.dist(i, j) for i in V for j in V if i != j}, 0.0)}


def variable_groups(inst: CVRPInstance):
    order = sorted(inst.customers, key=lambda c: math.atan2(inst.coords[c][1] - inst.coords[0][1],
                                                              inst.coords[c][0] - inst.coords[0][0]))
    sector = {c: k // 4 for k, c in enumerate(order)}
    groups = {f"s{k}": [] for k in range(max(sector.values()) + 1)}
    for v in structural_variables(inst):
        _, a, b = v.split("_")
        groups[f"s{sector[int(a) if int(a) else int(b)]}"].append(v)
    return groups
