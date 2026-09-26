from __future__ import annotations

from math import inf
from random import Random
from typing import Iterable

from examples.cvrp.instance import CVRPInstance


def canonical(sol):
    if isinstance(sol, tuple):
        return sol
    return tuple(sol)


def trivial_solution(inst):
    return tuple(inst.customers)


def random_solution(inst, rng):
    customers = list(inst.customers)
    rng.shuffle(customers)
    return tuple(customers)


def from_answer(inst, answer):
    tour: list[int] = []
    seen = set()
    for route in answer:
        for c in route:
            c = int(c)
            tour.append(c)
            seen.add(c)
    return canonical(tuple(tour))


def _as_tour(sol) -> tuple[int, ...]:
    return canonical(sol)


def _route_cost(inst: CVRPInstance, route: tuple[int, ...]) -> float:
    if not route:
        return 0.0
    total = inst.dist(0, route[0])
    for i in range(len(route) - 1):
        total += inst.dist(route[i], route[i + 1])
    total += inst.dist(route[-1], 0)
    return total


def _split_dp(inst: CVRPInstance, tour: tuple[int, ...]):
    n = len(tour)
    if n == 0:
        return [], 0.0

    demand = inst.demand
    cap = inst.capacity

    # Precompute segment costs and excess loads.
    seg_cost = [[inf] * (n + 1) for _ in range(n)]
    seg_excess = [[0.0] * (n + 1) for _ in range(n)]

    big_penalty = 1e6
    for i in range(n):
        load = 0.0
        for j in range(i + 1, n + 1):
            load += demand[tour[j - 1]]
            route = tour[i:j]
            c = _route_cost(inst, route)
            excess = max(0.0, load - cap)
            seg_excess[i][j] = excess
            seg_cost[i][j] = c + big_penalty * excess

    dp = [inf] * (n + 1)
    prev = [-1] * (n + 1)
    dp[0] = 0.0

    for j in range(1, n + 1):
        best = inf
        best_i = -1
        for i in range(0, j):
            cand = dp[i] + seg_cost[i][j]
            if cand < best:
                best = cand
                best_i = i
        dp[j] = best
        prev[j] = best_i

    routes: list[tuple[int, ...]] = []
    j = n
    while j > 0:
        i = prev[j]
        if i < 0:
            break
        routes.append(tour[i:j])
        j = i
    routes.reverse()
    return routes, dp[n]


def violations(inst, sol) -> dict[str, float]:
    tour = _as_tour(sol)
    n = inst.n_customers
    customers = set(inst.customers)

    counts = {c: 0 for c in customers}
    extra = 0
    for c in tour:
        if c in counts:
            counts[c] += 1
        else:
            extra += 1

    missing = sum(1 for c in customers if counts[c] == 0)
    duplicated = sum(max(0, counts[c] - 1) for c in customers)
    visita = float(missing + duplicated + extra)

    routes, _ = _split_dp(inst, tour)
    capacidad = 0.0
    for r in routes:
        load = sum(inst.demand[c] for c in r)
        capacidad += max(0.0, load - inst.capacity)

    return {"visita": float(visita), "capacidad": float(capacidad)}


def cost_terms(inst, sol) -> dict[str, float]:
    tour = _as_tour(sol)
    routes, split_cost = _split_dp(inst, tour)

    # Penalize violations so infeasible solutions are always worse than feasible ones.
    vio = violations(inst, tour)
    penalty = 1e6 * vio["visita"] + 1e6 * vio["capacidad"]

    return {"distancia": float(split_cost + penalty)}
