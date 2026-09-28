from __future__ import annotations

from random import Random
from typing import Any

from examples.cvrp.instance import CVRPInstance


def canonical(sol):
    routes = []
    for route in sol:
        if route:
            routes.append(tuple(int(c) for c in route))
    routes.sort(key=lambda r: r[0])
    return tuple(routes)


def trivial_solution(inst: CVRPInstance):
    return tuple((c,) for c in inst.customers)


def random_solution(inst: CVRPInstance, rng: Random):
    customers = list(inst.customers)
    rng.shuffle(customers)

    routes = []
    current = []
    current_load = 0.0
    for c in customers:
        d = inst.demand[c]
        if current and current_load + d > inst.capacity and rng.random() < 0.8:
            routes.append(tuple(current))
            current = [c]
            current_load = d
        else:
            current.append(c)
            current_load += d

    if current:
        routes.append(tuple(current))

    return canonical(routes)


def from_answer(inst: CVRPInstance, answer):
    return canonical(tuple(tuple(int(c) for c in route) for route in answer))


def violations(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)

    counts = [0] * (inst.n_customers + 1)
    for route in sol:
        for c in route:
            if 1 <= c <= inst.n_customers:
                counts[c] += 1
            else:
                counts[0] += 1  # out of range, counts as invalid extra visit

    visita = 0.0
    for c in inst.customers:
        visita += abs(counts[c] - 1)

    # Any invalid customer index is treated as a violation of visita as well
    visita += float(counts[0])

    capacidad = 0.0
    for route in sol:
        load = sum(inst.demand[c] for c in route if 1 <= c <= inst.n_customers)
        capacidad += max(0.0, load - inst.capacity)

    return {"visita": float(visita), "capacidad": float(capacidad)}


def cost_terms(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)

    distance = 0.0
    for route in sol:
        prev = 0
        for c in route:
            if 1 <= c <= inst.n_customers:
                distance += inst.dist(prev, c)
                prev = c
        distance += inst.dist(prev, 0)

    v = violations(inst, sol)
    penalty_scale = 1.0 + 1000.0 * (inst.n_customers + 1) * max(
        (inst.dist(i, j) for i in range(inst.n_customers + 1) for j in range(inst.n_customers + 1)),
        default=1.0,
    )
    penalized_distance = distance + penalty_scale * (v["visita"] + v["capacidad"])
    return {"distancia": float(penalized_distance)}
