from __future__ import annotations

from typing import Any
import random

from examples.cvrp.instance import CVRPInstance


COMPONENT = {
    "name": "cvrp_heuristic_view",
    "slot": "heuristic_view",
    "compatible_skeletons": ["generic"],
    "requires": ["problem_model"],
    "params": {},
}


def _normalize_route(route: Any) -> tuple[int, ...]:
    return tuple(int(c) for c in route)


def _normalize_solution(sol: Any) -> tuple[tuple[int, ...], ...]:
    routes = []
    for route in sol:
        r = _normalize_route(route)
        if r:
            routes.append(r)
    routes.sort()
    return tuple(routes)


def canonical(sol):
    return _normalize_solution(sol)


def trivial_solution(inst: CVRPInstance):
    routes = tuple((c,) for c in inst.customers)
    return canonical(routes)


def random_solution(inst: CVRPInstance, rng: random.Random):
    customers = list(inst.customers)
    rng.shuffle(customers)

    routes = []
    route = []
    load = 0.0

    for c in customers:
        d = inst.demand[c]
        if route and load + d > inst.capacity:
            routes.append(tuple(route))
            route = [c]
            load = d
        else:
            route.append(c)
            load += d

        if route and rng.random() < 0.25:
            routes.append(tuple(route))
            route = []
            load = 0.0

    if route:
        routes.append(tuple(route))

    if not routes:
        routes = [(c,) for c in customers]

    return canonical(routes)


def from_answer(inst: CVRPInstance, answer):
    return canonical(answer)


def violations(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)

    counts = {c: 0 for c in inst.customers}
    cap_excess = 0.0

    for route in sol:
        load = 0.0
        for c in route:
            if c in counts:
                counts[c] += 1
                load += inst.demand[c]
        cap_excess += max(0.0, load - inst.capacity)

    visita = sum(abs(count - 1) for count in counts.values())
    return {"visita": float(visita), "capacidad": float(cap_excess)}


def cost_terms(inst: CVRPInstance, sol) -> dict[str, float]:
    sol = canonical(sol)
    dist = 0.0

    for route in sol:
        prev = 0
        for c in route:
            dist += inst.dist(prev, c)
            prev = c
        dist += inst.dist(prev, 0)

    return {"distancia": float(dist)}
