import random as _random
from examples.cvrp.instance import CVRPInstance


def canonical(sol):
    routes = []
    for r in sol:
        t = tuple(int(c) for c in r)
        if t:
            routes.append(t)
    routes.sort(key=lambda t: (t[0], t))
    return tuple(routes)


def trivial_solution(inst):
    return canonical([(c,) for c in inst.customers])


def random_solution(inst, rng):
    custs = list(inst.customers)
    rng.shuffle(custs)
    routes = []
    cur = []
    load = 0.0
    for c in custs:
        d = inst.demand[c]
        if cur and (load + d > inst.capacity or rng.random() < 0.1):
            routes.append(cur)
            cur = []
            load = 0.0
        cur.append(c)
        load += d
    if cur:
        routes.append(cur)
    return canonical(routes)


def from_answer(inst, answer):
    return canonical(answer)


def _valid(inst, c):
    return 1 <= c <= inst.n_customers


def violations(inst, sol):
    n = inst.n_customers
    counts = [0] * (n + 1)
    invalid = 0
    cap_excess = 0.0
    for r in sol:
        load = 0.0
        for c in r:
            c = int(c)
            if 1 <= c <= n:
                counts[c] += 1
                load += inst.demand[c]
            else:
                invalid += 1
        if load > inst.capacity:
            cap_excess += load - inst.capacity
    visit = invalid + sum(abs(counts[c] - 1) for c in range(1, n + 1))
    return {"visita": float(visit), "capacidad": float(cap_excess)}


def cost_terms(inst, sol):
    total = 0.0
    for r in sol:
        nodes = [int(c) for c in r if _valid(inst, int(c))]
        if not nodes:
            continue
        prev = 0
        for c in nodes:
            total += inst.dist(prev, c)
            prev = c
        total += inst.dist(prev, 0)
    return {"distancia": total}
