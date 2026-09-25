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
