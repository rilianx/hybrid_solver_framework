import functools
import random as _random

from examples.cvrp.instance import CVRPInstance


def canonical(sol):
    return tuple(int(c) for c in sol)


def trivial_solution(inst):
    return tuple(range(1, inst.n_customers + 1))


def random_solution(inst, rng):
    perm = list(range(1, inst.n_customers + 1))
    rng.shuffle(perm)
    return tuple(perm)


def from_answer(inst, answer):
    tour = []
    for route in answer:
        for c in route:
            tour.append(int(c))
    return tuple(tour)


@functools.lru_cache(maxsize=4096)
def _split(inst, tour):
    """Split de Prins. Devuelve (rutas, distancia total). Ignora ids inválidos."""
    n = inst.n_customers
    nodes = [c for c in tour if 1 <= c <= n]
    m = len(nodes)
    if m == 0:
        return (), 0.0
    cap = inst.capacity
    dem = inst.demand
    dist = inst.dist
    INF = float("inf")
    best = [INF] * (m + 1)
    pred = [-1] * (m + 1)
    best[0] = 0.0
    for i in range(m):
        if best[i] == INF:
            continue
        load = 0.0
        cost = 0.0
        prev = 0
        base = best[i]
        for j in range(i, m):
            c = nodes[j]
            load += dem[c]
            if j > i and load > cap + 1e-9:
                break
            cost += dist(prev, c)
            prev = c
            total = base + cost + dist(c, 0)
            if total < best[j + 1] - 1e-12:
                best[j + 1] = total
                pred[j + 1] = i
    routes = []
    j = m
    while j > 0:
        i = pred[j]
        routes.append(tuple(nodes[i:j]))
        j = i
    routes.reverse()
    return tuple(routes), best[m]


def _decode(inst, sol):
    return _split(inst, canonical(sol))


def violations(inst, sol):
    sol = canonical(sol)
    n = inst.n_customers
    counts = [0] * (n + 1)
    invalid = 0
    for c in sol:
        if 1 <= c <= n:
            counts[c] += 1
        else:
            invalid += 1
    visita = float(invalid + sum(abs(counts[c] - 1) for c in range(1, n + 1)))
    routes, _ = _decode(inst, sol)
    cap = inst.capacity
    exceso = 0.0
    for r in routes:
        load = sum(inst.demand[c] for c in r)
        if load > cap:
            exceso += load - cap
    return {"visita": visita, "capacidad": float(exceso)}


def cost_terms(inst, sol):
    _, d = _decode(inst, sol)
    return {"distancia": float(d)}
