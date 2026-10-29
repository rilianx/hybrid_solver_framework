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


# ---- vista MIP ----
import math


def _arcs(inst):
    N = len(inst.coords)
    return [(i, j) for i in range(N) for j in range(N) if i != j]


def _xn(i, j):
    return f"x_{i}_{j}"


def _fn(i, j):
    return f"f_{i}_{j}"


def _flow_ub(inst):
    total = float(sum(inst.demand))
    return max(inst.capacity, total) * max(1, inst.n_customers) + inst.capacity


def variables(inst):
    v = {}
    fub = _flow_ub(inst)
    for i, j in _arcs(inst):
        v[_xn(i, j)] = (0.0, 1.0, "binary")
    for i, j in _arcs(inst):
        v[_fn(i, j)] = (0.0, fub, "continuous")
    v["bad"] = (0.0, float(max(1, 10 * (inst.n_customers + 1))), "continuous")
    return v


def structural_variables(inst):
    return [_xn(i, j) for i, j in _arcs(inst)]


def _decoded_routes(inst, sol):
    routes, _ = _decode(inst, sol)
    return routes


def to_assignment(inst, sol):
    x = {_xn(i, j): 0.0 for i, j in _arcs(inst)}
    for r in _decoded_routes(inst, sol):
        path = [0] + list(r) + [0]
        for a, b in zip(path, path[1:]):
            if a != b:
                x[_xn(a, b)] += 1.0
    return x


def aux_values(inst, sol):
    sol = canonical(sol)
    n = inst.n_customers
    vals = {_fn(i, j): 0.0 for i, j in _arcs(inst)}
    dem = inst.demand
    for r in _decoded_routes(inst, sol):
        remaining = float(sum(dem[c] for c in r))
        path = [0] + list(r) + [0]
        for a, b in zip(path, path[1:]):
            if a != b:
                vals[_fn(a, b)] += remaining
            if b != 0:
                remaining -= dem[b]
    vals["bad"] = float(sum(1 for c in sol if not (1 <= c <= n)))
    return vals


def from_assignment(inst, x):
    n = inst.n_customers
    N = n + 1
    succ = {}
    starts = []
    for i, j in _arcs(inst):
        if x.get(_xn(i, j), 0.0) > 0.5:
            if i == 0:
                starts.append(j)
            else:
                succ.setdefault(i, j)
    tour = []
    seen = set()
    for s in starts:
        c = s
        steps = 0
        while c != 0 and c not in seen and steps <= N:
            seen.add(c)
            tour.append(c)
            c = succ.get(c, 0)
            steps += 1
    for c in range(1, N):
        if c not in seen:
            tour.append(c)
    return tuple(tour)


def constraint_families(inst):
    N = len(inst.coords)
    cust = list(range(1, N))
    Q = float(inst.capacity)
    fam = {}
    ent, sal, cons = [], [], []
    for j in cust:
        ent.append(({_xn(i, j): 1.0 for i in range(N) if i != j}, "==", 1.0))
        sal.append(({_xn(j, k): 1.0 for k in range(N) if k != j}, "==", 1.0))
        co = {}
        for i in range(N):
            if i != j:
                co[_fn(i, j)] = co.get(_fn(i, j), 0.0) + 1.0
                co[_fn(j, i)] = co.get(_fn(j, i), 0.0) - 1.0
        cons.append((co, "==", float(inst.demand[j])))
    dep = {}
    for j in cust:
        dep[_xn(0, j)] = 1.0
        dep[_xn(j, 0)] = -1.0
    fam["visita.entrada"] = ent
    fam["visita.salida"] = sal
    fam["visita.flujo"] = cons
    fam["visita.deposito"] = [(dep, "==", 0.0)] if cust else []
    fam["visita.ids"] = [({"bad": 1.0}, "<=", 0.0)]
    fam["capacidad"] = [({_fn(i, j): 1.0, _xn(i, j): -Q}, "<=", 0.0) for i, j in _arcs(inst)]
    return fam


def objective_terms(inst):
    return {"distancia": ({_xn(i, j): float(inst.dist(i, j)) for i, j in _arcs(inst)}, 0.0)}


def variable_groups(inst):
    n = inst.n_customers
    struct = structural_variables(inst)
    if n < 4:
        k = 4
        groups = {f"g{g}": [] for g in range(k)}
        for idx, v in enumerate(struct):
            groups[f"g{idx % k}"].append(v)
        return {g: vs for g, vs in groups.items() if vs}
    x0, y0 = inst.coords[0]
    order = sorted(range(1, n + 1),
                   key=lambda c: (math.atan2(inst.coords[c][1] - y0, inst.coords[c][0] - x0), c))
    k = n if n <= 12 else max(4, math.ceil(n / 3))
    gid = {}
    for pos, c in enumerate(order):
        gid[c] = pos * k // n
    groups = {f"g{g}": [] for g in range(k)}
    for i, j in _arcs(inst):
        g = gid[i] if i != 0 else gid[j]
        groups[f"g{g}"].append(_xn(i, j))
    return {g: vs for g, vs in groups.items() if vs}


# ---- vista constructiva ----
def empty_partial(inst):
    # (tour, carga de la ruta actual, último nodo de la ruta actual; 0 = ninguna ruta abierta)
    return ((), 0.0, 0)


def candidates(inst, partial):
    tour, load, last = partial
    n = inst.n_customers
    seen = set(tour)
    cap = inst.capacity
    dem = inst.demand
    dist = inst.dist
    out = []
    for c in range(1, n + 1):
        if c in seen:
            continue
        new_delta = dist(0, c) + dist(c, 0)
        # Abrir una ruta nueva con c (siempre posible: el split lo respeta)
        out.append((c, True, float(new_delta)))
        # Continuar la ruta actual si cabe
        if last != 0 and load + dem[c] <= cap + 1e-9:
            delta = dist(last, c) + dist(c, 0) - dist(last, 0)
            out.append((c, False, float(delta)))
    return out


def apply_action(inst, partial, action):
    tour, load, last = partial
    c, new_route, _ = action
    c = int(c)
    if new_route or last == 0:
        return (tour + (c,), float(inst.demand[c]), c)
    return (tour + (c,), float(load + inst.demand[c]), c)


def is_complete(inst, partial):
    return len(partial[0]) >= inst.n_customers


def to_solution(inst, partial):
    return canonical(partial[0])


def complete_partial(inst, partial, rng):
    tour = list(partial[0])
    seen = set(tour)
    rest = [c for c in range(1, inst.n_customers + 1) if c not in seen]
    # Completar por vecino más cercano desde el último nodo; el split garantiza capacidad.
    last = tour[-1] if tour else 0
    dist = inst.dist
    remaining = set(rest)
    while remaining:
        nxt = min(remaining, key=lambda x: (dist(last, x), x))
        tour.append(nxt)
        remaining.discard(nxt)
        last = nxt
    return canonical(tour)
