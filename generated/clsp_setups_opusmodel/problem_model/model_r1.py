from functools import lru_cache

from examples.lotsizing.instance import CLSPInstance

_EPS = 1e-9


def canonical(sol):
    return tuple(tuple(bool(v) for v in row) for row in sol)


def trivial_solution(inst):
    return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def random_solution(inst, rng):
    return tuple(tuple(rng.random() < 0.5 for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def from_answer(inst, answer):
    return tuple(tuple(bool(int(v)) for v in row) for row in answer)


@lru_cache(maxsize=4096)
def _evaluate(inst, plan):
    """Min-cost max-flow: devuelve (demanda_no_cubierta, exceso_setup, costo_setup, costo_inv)."""
    n, T = inst.n_items, inst.n_periods
    d = inst.demand
    total_d = sum(sum(r) for r in d)
    big = total_d + 1.0

    setup_c = 0.0
    excess = 0.0
    avail = []
    for t in range(T):
        stt = 0.0
        for i in range(n):
            if plan[i][t]:
                stt += inst.setup_time[i]
                setup_c += inst.setup_cost[i]
        rem = inst.capacity[t] - stt
        if rem < 0:
            excess += -rem
            rem = 0.0
        avail.append(rem)

    S = 0
    sink = 1 + T + n * T
    N = sink + 1
    to, cap, cost = [], [], []
    adj = [[] for _ in range(N)]

    def add(u, v, c, w):
        adj[u].append(len(to)); to.append(v); cap.append(c); cost.append(w)
        adj[v].append(len(to)); to.append(u); cap.append(0.0); cost.append(-w)

    def ip(i, t):
        return 1 + T + i * T + t

    for t in range(T):
        if avail[t] > _EPS:
            add(S, 1 + t, avail[t], 0.0)
    for i in range(n):
        for t in range(T):
            if plan[i][t]:
                add(1 + t, ip(i, t), big, 0.0)
            if t + 1 < T:
                add(ip(i, t), ip(i, t + 1), big, float(inst.holding_cost[i]))
            if d[i][t] > _EPS:
                add(ip(i, t), sink, float(d[i][t]), 0.0)

    flow = 0.0
    inv_cost = 0.0
    while True:
        dist = [float("inf")] * N
        inq = [False] * N
        prev = [-1] * N
        dist[S] = 0.0
        q = [S]
        inq[S] = True
        head = 0
        while head < len(q):
            u = q[head]; head += 1
            inq[u] = False
            du = dist[u]
            for e in adj[u]:
                if cap[e] > _EPS:
                    v = to[e]
                    nd = du + cost[e]
                    if nd < dist[v] - 1e-12:
                        dist[v] = nd
                        prev[v] = e
                        if not inq[v]:
                            inq[v] = True
                            q.append(v)
        if dist[sink] == float("inf"):
            break
        f = float("inf")
        v = sink
        while v != S:
            e = prev[v]
            f = min(f, cap[e])
            v = to[e ^ 1]
        if f <= _EPS:
            break
        v = sink
        while v != S:
            e = prev[v]
            cap[e] -= f
            cap[e ^ 1] += f
            v = to[e ^ 1]
        flow += f
        inv_cost += f * dist[sink]

    unmet = max(0.0, total_d - flow)
    if unmet < 1e-6:
        unmet = 0.0
    return unmet, excess, setup_c, inv_cost


def violations(inst, sol):
    plan = canonical(sol)
    unmet, excess, _, _ = _evaluate(inst, plan)
    return {"demanda": round(unmet + excess, 9)}


def cost_terms(inst, sol):
    plan = canonical(sol)
    _, _, sc, ic = _evaluate(inst, plan)
    return {"setup": round(sc, 9), "inventario": round(ic, 9)}


# ---- vista MIP ----
import math
from functools import lru_cache as _lru_cache_mip


def _yn(i, t):
    return f"y_{i}_{t}"


def _xn(i, t):
    return f"x_{i}_{t}"


def _In(i, t):
    return f"I_{i}_{t}"


def _rem_demand(inst, i, t):
    return float(sum(inst.demand[i][t:]))


def _prod_ub(inst, i, t):
    return max(0.0, min(float(inst.capacity[t]), _rem_demand(inst, i, t)))


def _inv_ub(inst, i, t):
    return max(0.0, _rem_demand(inst, i, t + 1))


def variables(inst):
    n, T = inst.n_items, inst.n_periods
    v = {}
    for i in range(n):
        for t in range(T):
            v[_yn(i, t)] = (0.0, 1.0, "binary")
    for i in range(n):
        for t in range(T):
            v[_xn(i, t)] = (0.0, _prod_ub(inst, i, t), "continuous")
            if t + 1 < T:
                v[_In(i, t)] = (0.0, _inv_ub(inst, i, t), "continuous")
    return v


def structural_variables(inst):
    return [_yn(i, t) for i in range(inst.n_items) for t in range(inst.n_periods)]


def to_assignment(inst, sol):
    plan = canonical(sol)
    return {_yn(i, t): (1.0 if plan[i][t] else 0.0)
            for i in range(inst.n_items) for t in range(inst.n_periods)}


def from_assignment(inst, x):
    return tuple(tuple(float(x.get(_yn(i, t), 0.0)) > 0.5 for t in range(inst.n_periods))
                 for i in range(inst.n_items))


@_lru_cache_mip(maxsize=4096)
def _flows(inst, plan):
    """Mismo flujo de costo mínimo que _evaluate, devolviendo producción e inventarios."""
    n, T = inst.n_items, inst.n_periods
    d = inst.demand
    total_d = sum(sum(r) for r in d)
    big = total_d + 1.0
    avail = []
    for t in range(T):
        stt = 0.0
        for i in range(n):
            if plan[i][t]:
                stt += inst.setup_time[i]
        rem = inst.capacity[t] - stt
        if rem < 0:
            rem = 0.0
        avail.append(rem)

    S = 0
    sink = 1 + T + n * T
    N = sink + 1
    to, cap, cost, orig = [], [], [], []
    adj = [[] for _ in range(N)]

    def add(u, v, c, w):
        e = len(to)
        adj[u].append(len(to)); to.append(v); cap.append(c); cost.append(w); orig.append(c)
        adj[v].append(len(to)); to.append(u); cap.append(0.0); cost.append(-w); orig.append(0.0)
        return e

    def ip(i, t):
        return 1 + T + i * T + t

    prod_e, inv_e = {}, {}
    for t in range(T):
        if avail[t] > _EPS:
            add(S, 1 + t, avail[t], 0.0)
    for i in range(n):
        for t in range(T):
            if plan[i][t]:
                prod_e[(i, t)] = add(1 + t, ip(i, t), big, 0.0)
            if t + 1 < T:
                inv_e[(i, t)] = add(ip(i, t), ip(i, t + 1), big, float(inst.holding_cost[i]))
            if d[i][t] > _EPS:
                add(ip(i, t), sink, float(d[i][t]), 0.0)

    while True:
        dist = [float("inf")] * N
        inq = [False] * N
        prev = [-1] * N
        dist[S] = 0.0
        q = [S]
        inq[S] = True
        head = 0
        while head < len(q):
            u = q[head]; head += 1
            inq[u] = False
            du = dist[u]
            for e in adj[u]:
                if cap[e] > _EPS:
                    v = to[e]
                    nd = du + cost[e]
                    if nd < dist[v] - 1e-12:
                        dist[v] = nd
                        prev[v] = e
                        if not inq[v]:
                            inq[v] = True
                            q.append(v)
        if dist[sink] == float("inf"):
            break
        f = float("inf")
        v = sink
        while v != S:
            e = prev[v]
            f = min(f, cap[e])
            v = to[e ^ 1]
        if f <= _EPS:
            break
        v = sink
        while v != S:
            e = prev[v]
            cap[e] -= f
            cap[e ^ 1] += f
            v = to[e ^ 1]

    xs, Is = {}, {}
    for i in range(n):
        for t in range(T):
            e = prod_e.get((i, t))
            xs[(i, t)] = max(0.0, orig[e] - cap[e]) if e is not None else 0.0
            if t + 1 < T:
                e = inv_e[(i, t)]
                Is[(i, t)] = max(0.0, orig[e] - cap[e])
    return tuple(sorted(xs.items())), tuple(sorted(Is.items()))


def aux_values(inst, sol):
    plan = canonical(sol)
    xs, Is = _flows(inst, plan)
    out = {}
    for (i, t), val in xs:
        out[_xn(i, t)] = val
    for (i, t), val in Is:
        out[_In(i, t)] = val
    return out


def constraint_families(inst):
    n, T = inst.n_items, inst.n_periods
    bal, capc, link = [], [], []
    for i in range(n):
        for t in range(T):
            coefs = {_xn(i, t): 1.0}
            if t > 0:
                coefs[_In(i, t - 1)] = 1.0
            if t + 1 < T:
                coefs[_In(i, t)] = -1.0
            bal.append((coefs, "==", float(inst.demand[i][t])))
            M = _prod_ub(inst, i, t)
            link.append(({_xn(i, t): 1.0, _yn(i, t): -M}, "<=", 0.0))
    for t in range(T):
        coefs = {}
        for i in range(n):
            coefs[_xn(i, t)] = 1.0
            coefs[_yn(i, t)] = float(inst.setup_time[i])
        capc.append((coefs, "<=", float(inst.capacity[t])))
    return {"demanda.balance": bal, "demanda.capacidad": capc, "demanda.setup": link}


def objective_terms(inst):
    n, T = inst.n_items, inst.n_periods
    setup = {_yn(i, t): float(inst.setup_cost[i]) for i in range(n) for t in range(T)}
    inv = {_In(i, t): float(inst.holding_cost[i]) for i in range(n) for t in range(T - 1)}
    return {"setup": (setup, 0.0), "inventario": (inv, 0.0)}


def variable_groups(inst):
    n, T = inst.n_items, inst.n_periods
    N = n * T
    if N < 4:
        return {f"g{k}": [v] for k, v in enumerate(structural_variables(inst))}
    c = min(n, max(1, (n * T) // 4), 10)
    groups = {}
    for t in range(T):
        for k, start in enumerate(range(0, n, c)):
            groups[f"p{t}_b{k}"] = [_yn(i, t) for i in range(start, min(n, start + c))]
    return groups
