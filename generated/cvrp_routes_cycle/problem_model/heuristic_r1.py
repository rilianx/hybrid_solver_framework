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
