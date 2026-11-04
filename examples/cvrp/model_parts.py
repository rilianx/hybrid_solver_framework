"""El oráculo del CVRP (`core.model_parts`, vista heurística): la referencia contra la que se valida lo que escribe el
LLM y con la que se generan los casos de prueba (`cases.py`).

Formato neutral de respuesta (el de los casos): lista de rutas, cada una una lista de clientes
en orden de visita, sin el depósito. Familias: `visita` (cada cliente exactamente una vez) y
`capacidad` (carga de cada ruta <= Q). Términos del objetivo: `distancia`.

La vista MIP la escribe el LLM (`llm.native_mip_generator`, `generated/cvrp_native/mip/mip.py`).
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


# ---------------------------------------------------------------- vista constructiva
# La de `construction.py` (inserción de un cliente en una ruta donde cabe, o ruta nueva).
def _view(inst: CVRPInstance):
    from .construction import CVRPConstructionView

    return CVRPConstructionView(None, inst)


def empty_partial(inst: CVRPInstance):
    return _view(inst).empty()


def candidates(inst: CVRPInstance, partial):
    return _view(inst).candidates(partial)


def apply_action(inst: CVRPInstance, partial, action):
    return _view(inst).apply(partial, action)


def is_complete(inst: CVRPInstance, partial) -> bool:
    return _view(inst).is_complete(partial)


def to_solution(inst: CVRPInstance, partial):
    return canonical(partial.routes)


def complete_partial(inst: CVRPInstance, partial, rng):
    return canonical([*partial.routes, *([c] for c in sorted(partial.pending))])
