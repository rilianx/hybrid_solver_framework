import math

from examples.lotsizing.model_parts import _plan, canonical


def _yn(i, t):
    return f"y_{i}_{t}"


def _xn(i, t):
    return f"x_{i}_{t}"


def _sn(i, t):
    return f"s_{i}_{t}"


def _bigM(inst, i, t):
    rem = sum(inst.demand[i][k] for k in range(t, inst.n_periods))
    return max(0.0, min(inst.capacity[t] - inst.setup_time[i], rem))


def variables(inst):
    v = {}
    I, T = range(inst.n_items), range(inst.n_periods)
    for i in I:
        for t in T:
            v[_yn(i, t)] = (0.0, 1.0, "binary")
    for i in I:
        for t in T:
            v[_xn(i, t)] = (0.0, float("inf"), "continuous")
            v[_sn(i, t)] = (0.0, float("inf"), "continuous")
    return v


def structural_variables(inst):
    return [_yn(i, t) for i in range(inst.n_items) for t in range(inst.n_periods)]


def to_assignment(inst, sol):
    sol = canonical(sol)
    return {_yn(i, t): (1.0 if sol[i][t] else 0.0)
            for i in range(inst.n_items) for t in range(inst.n_periods)}


def aux_values(inst, sol):
    sol = canonical(sol)
    xs, ss, _ = _plan(inst, sol)
    I, T = range(inst.n_items), range(inst.n_periods)
    out = {}
    for i in I:
        x = [float(xs[i, t]) for t in T]
        s = [float(ss[i, t]) for t in T]
        # Remove surplus production (only relevant when holding cost is 0)
        for t in reversed(list(T)):
            if x[t] <= 0:
                continue
            m = min(s[k] for k in range(t, inst.n_periods))
            d = min(x[t], m)
            if d > 0:
                x[t] -= d
                for k in range(t, inst.n_periods):
                    s[k] -= d
        for t in T:
            out[_xn(i, t)] = max(0.0, x[t])
            out[_sn(i, t)] = max(0.0, s[t])
    return out


def from_assignment(inst, x):
    return tuple(tuple(float(x.get(_yn(i, t), 0.0)) > 0.5 for t in range(inst.n_periods))
                 for i in range(inst.n_items))


def constraint_families(inst):
    I, T = range(inst.n_items), range(inst.n_periods)
    dem, cap, link = [], [], []
    for i in I:
        for t in T:
            coefs = {_xn(i, t): 1.0, _sn(i, t): -1.0}
            if t > 0:
                coefs[_sn(i, t - 1)] = 1.0
            dem.append((coefs, "==", float(inst.demand[i][t])))
    for t in T:
        coefs = {}
        for i in I:
            coefs[_xn(i, t)] = 1.0
            coefs[_yn(i, t)] = float(inst.setup_time[i])
        cap.append((coefs, "<=", float(inst.capacity[t])))
    for i in I:
        for t in T:
            M = _bigM(inst, i, t)
            link.append(({_xn(i, t): 1.0, _yn(i, t): -M}, "<=", 0.0))
    return {"demanda": dem, "capacidad": cap, "enlace": link}


def objective_terms(inst):
    I, T = range(inst.n_items), range(inst.n_periods)
    setup = {_yn(i, t): float(inst.setup_cost[i]) for i in I for t in T}
    inv = {_sn(i, t): float(inst.holding_cost[i]) for i in I for t in T}
    return {"setup": (setup, 0.0), "inventario": (inv, 0.0)}


def variable_groups(inst):
    order = [_yn(i, t) for t in range(inst.n_periods) for i in range(inst.n_items)]
    N = len(order)
    if N == 0:
        return {}
    k = min(N, max(4, math.ceil(N / 12)))
    while k < N and math.ceil(N / k) > N / 3:
        k += 1
    base, extra = divmod(N, k)
    groups = {}
    pos = 0
    for g in range(k):
        size = base + (1 if g < extra else 0)
        if size == 0:
            continue
        groups[f"bloque_{g}"] = order[pos:pos + size]
        pos += size
    return groups
