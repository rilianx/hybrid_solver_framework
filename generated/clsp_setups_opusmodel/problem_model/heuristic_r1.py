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
