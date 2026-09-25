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
