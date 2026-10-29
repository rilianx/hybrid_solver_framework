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


# ---- vista MIP ----
import math as _math
import functools as _functools


@_functools.lru_cache(maxsize=64)
def _arc_list(inst):
    N = inst.n_customers + 1
    return tuple((i, j) for i in range(N) for j in range(N) if i != j)


def _xn(i, j):
    return f"x_{i}_{j}"


def _fn(i, j):
    return f"f_{i}_{j}"


def _route_traversals(inst, sol):
    """arc -> lista de cargas remanentes (tras llegar a j) de cada recorrido del arco."""
    trav = {}
    self_loops = 0
    for r in sol:
        nodes = [int(c) for c in r if _valid(inst, int(c))]
        if not nodes:
            continue
        m = len(nodes)
        suffix = [0.0] * (m + 1)
        for k in range(m - 1, -1, -1):
            suffix[k] = suffix[k + 1] + inst.demand[nodes[k]]
        seq = [0] + nodes + [0]
        for k in range(len(seq) - 1):
            a, b = seq[k], seq[k + 1]
            if a == b:
                self_loops += 1
                continue
            rem = suffix[k] if b != 0 else 0.0
            trav.setdefault((a, b), []).append(rem)
    return trav


def variables(inst):
    V = {}
    tot = float(sum(inst.demand))
    for (i, j) in _arc_list(inst):
        V[_xn(i, j)] = (0.0, 1.0, "binary")
    for (i, j) in _arc_list(inst):
        if j != 0:
            V[_fn(i, j)] = (0.0, max(tot, float(inst.capacity)), "continuous")
    big = 1e9
    V["extra_dist"] = (0.0, big, "continuous")
    V["visit_err"] = (0.0, big, "continuous")
    return V


def structural_variables(inst):
    return [_xn(i, j) for (i, j) in _arc_list(inst)]


def to_assignment(inst, sol):
    trav = _route_traversals(inst, sol)
    return {_xn(i, j): (1.0 if (i, j) in trav else 0.0) for (i, j) in _arc_list(inst)}


def aux_values(inst, sol):
    trav = _route_traversals(inst, sol)
    out = {}
    for (i, j) in _arc_list(inst):
        if j != 0:
            lst = trav.get((i, j))
            out[_fn(i, j)] = float(max(lst)) if lst else 0.0
    extra = 0.0
    for (i, j), lst in trav.items():
        if len(lst) > 1:
            extra += (len(lst) - 1) * inst.dist(i, j)
    out["extra_dist"] = extra
    out["visit_err"] = float(violations(inst, sol)["visita"])
    return out


def from_assignment(inst, x):
    n = inst.n_customers
    succ = {}
    for (i, j) in _arc_list(inst):
        if x.get(_xn(i, j), 0.0) > 0.5:
            succ.setdefault(i, []).append(j)
    routes = []
    seen = set()
    for start in sorted(succ.get(0, [])):
        if start in seen:
            continue
        route = []
        cur = start
        while cur != 0 and cur not in seen and 1 <= cur <= n:
            seen.add(cur)
            route.append(cur)
            nxt = succ.get(cur, [0])
            cur = nxt[0]
        if route:
            routes.append(route)
    return canonical(routes)


def constraint_families(inst):
    n = inst.n_customers
    N = n + 1
    Q = float(inst.capacity)
    d = inst.demand
    arcs = _arc_list(inst)
    ent, sal, flu = [], [], []
    for j in range(1, N):
        ent.append(({_xn(i, j): 1.0 for i in range(N) if i != j}, "==", 1.0))
        sal.append(({_xn(j, k): 1.0 for k in range(N) if k != j}, "==", 1.0))
        co = {}
        for i in range(N):
            if i != j:
                co[_fn(i, j)] = co.get(_fn(i, j), 0.0) + 1.0
        for k in range(1, N):
            if k != j:
                co[_fn(j, k)] = co.get(_fn(j, k), 0.0) - 1.0
        flu.append((co, "==", float(d[j])))
    cap_up, cap_lo = [], []
    for (i, j) in arcs:
        if j == 0:
            continue
        cap_up.append(({_fn(i, j): 1.0, _xn(i, j): -(Q - float(d[i]))}, "<=", 0.0))
        cap_lo.append(({_fn(i, j): 1.0, _xn(i, j): -float(d[j])}, ">=", 0.0))
    return {
        "visita.entrada": ent,
        "visita.salida": sal,
        "visita.flujo": flu,
        "visita.extra": [({"extra_dist": 1.0}, "<=", 0.0)],
        "visita.conteo": [({"visit_err": 1.0}, "<=", 0.0)],
        "capacidad.carga": cap_up,
        "capacidad.minimo": cap_lo,
    }


def objective_terms(inst):
    co = {_xn(i, j): inst.dist(i, j) for (i, j) in _arc_list(inst)}
    co["extra_dist"] = 1.0
    return {"distancia": (co, 0.0)}


def variable_groups(inst):
    n = inst.n_customers
    names = structural_variables(inst)
    if n < 4:
        L = len(names)
        k = max(4, L) if L <= 4 else L
        size = max(1, L // 4) if L >= 12 else 1
        groups = {}
        for idx in range(0, L, size):
            groups[f"g{len(groups)}"] = names[idx:idx + size]
        return groups
    x0, y0 = inst.coords[0]
    custs = sorted(inst.customers,
                   key=lambda c: (_math.atan2(inst.coords[c][1] - y0, inst.coords[c][0] - x0), c))
    k = max(4, -(-n // 5))
    while k < n and -(-n // k) * 3 > n:
        k += 1
    k = min(k, n)
    base, rem = divmod(n, k)
    owner = {}
    pos = 0
    for g in range(k):
        sz = base + (1 if g < rem else 0)
        for c in custs[pos:pos + sz]:
            owner[c] = g
        pos += sz
    groups = {f"g{g}": [] for g in range(k)}
    for (i, j) in _arc_list(inst):
        key = i if i != 0 else j
        groups[f"g{owner[key]}"].append(_xn(i, j))
    return {g: v for g, v in groups.items() if v}


# ---- vista constructiva ----
def empty_partial(inst):
    # (rutas cerradas, ruta actual, carga actual, clientes pendientes ordenados)
    return ((), (), 0.0, tuple(inst.customers))


def candidates(inst, partial):
    closed, cur, load, remaining = partial
    if not remaining:
        return []
    last = cur[-1] if cur else 0
    cap = inst.capacity + 1e-9
    acts = []
    for c in remaining:
        d = inst.demand[c]
        if load + d <= cap:
            # aumento de costo suponiendo que la ruta volverá al depósito después de c
            delta = inst.dist(last, c) + inst.dist(c, 0) - inst.dist(last, 0)
            acts.append(("add", c, delta, load + d))
    if cur:
        acts.append(("close", None, 0.0, 0.0))
    return acts


def apply_action(inst, partial, action):
    closed, cur, load, remaining = partial
    kind = action[0]
    if kind == "close":
        if not cur:
            return partial
        return (closed + (cur,), (), 0.0, remaining)
    c = int(action[1])
    new_rem = tuple(x for x in remaining if x != c)
    return (closed, cur + (c,), load + inst.demand[c], new_rem)


def is_complete(inst, partial):
    return not partial[3]


def to_solution(inst, partial):
    closed, cur, load, remaining = partial
    routes = list(closed)
    if cur:
        routes.append(cur)
    return canonical(routes)


def complete_partial(inst, partial, rng):
    closed, cur, load, remaining = partial
    routes = [list(r) for r in closed]
    cap = inst.capacity + 1e-9
    cur = list(cur)
    rem = list(remaining)
    rng.shuffle(rem)
    open_routes = []  # [route, load]
    if cur:
        open_routes.append([cur, load])
    for c in rem:
        d = inst.demand[c]
        placed = False
        for r in open_routes:
            if r[1] + d <= cap:
                r[0].append(c)
                r[1] += d
                placed = True
                break
        if not placed:
            open_routes.append([[c], d])
    for r, _ in open_routes:
        routes.append(r)
    return canonical(routes)
