from examples.lotsizing.model_parts import canonical, _plan


def _y(i, t):
    return f"y_{i}_{t}"


def _x(i, t):
    return f"x_{i}_{t}"


def _s(i, t):
    return f"s_{i}_{t}"


def _rem(inst, i, t, l=None):
    """Demanda del ítem i en los períodos t..l (inclusive); l=None => hasta el final."""
    T = inst.n_periods
    if l is None:
        l = T - 1
    if t > l:
        return 0.0
    return float(sum(inst.demand[i][k] for k in range(t, l + 1)))


def variables(inst):
    I, T = range(inst.n_items), range(inst.n_periods)
    v = {}
    for i in I:
        for t in T:
            v[_y(i, t)] = (0.0, 1.0, "binary")
    for i in I:
        for t in T:
            ubx = max(0.0, min(float(inst.capacity[t]), _rem(inst, i, t)))
            v[_x(i, t)] = (0.0, ubx, "continuous")
            v[_s(i, t)] = (0.0, _rem(inst, i, t + 1), "continuous")
    return v


def structural_variables(inst):
    return [_y(i, t) for i in range(inst.n_items) for t in range(inst.n_periods)]


def to_assignment(inst, sol):
    sol = canonical(sol)
    return {_y(i, t): (1.0 if sol[i][t] else 0.0)
            for i in range(inst.n_items) for t in range(inst.n_periods)}


def aux_values(inst, sol):
    sol = canonical(sol)
    xs, ss, _ = _plan(inst, sol)
    I, T = inst.n_items, inst.n_periods
    out = {}
    for i in range(I):
        X = [float(xs[i, t]) for t in range(T)]
        S = [float(ss[i, t]) for t in range(T)]
        # Limpieza: con costo de inventario nulo el LP podría dejar stock final sobrante
        # (no cambia el costo); se elimina quitando producción desde el final.
        if inst.holding_cost[i] == 0 and S[T - 1] > 1e-9:
            e = S[T - 1]
            for k in range(T - 1, -1, -1):
                if e <= 1e-12:
                    break
                m = min(S[j] for j in range(k, T))
                a = min(e, X[k], m)
                if a > 0:
                    X[k] -= a
                    for j in range(k, T):
                        S[j] -= a
                    e -= a
        for t in range(T):
            out[_x(i, t)] = max(0.0, X[t])
            out[_s(i, t)] = max(0.0, S[t])
    return out


def from_assignment(inst, x):
    return tuple(
        tuple(bool(x.get(_y(i, t), 0.0) > 0.5) for t in range(inst.n_periods))
        for i in range(inst.n_items)
    )


def constraint_families(inst):
    I, T = range(inst.n_items), range(inst.n_periods)
    nT = inst.n_periods
    demanda, capacidad, enlace, ls = [], [], [], []
    # Balance de inventario (sin backlog, inventario inicial 0)
    for i in I:
        for t in T:
            c = {_x(i, t): 1.0, _s(i, t): -1.0}
            if t > 0:
                c[_s(i, t - 1)] = 1.0
            demanda.append((c, "==", float(inst.demand[i][t])))
    # Capacidad compartida
    for t in T:
        c = {}
        for i in I:
            c[_x(i, t)] = 1.0
            c[_y(i, t)] = float(inst.setup_time[i])
        capacidad.append((c, "<=", float(inst.capacity[t])))
    # Enlace producción-setup con big-M ajustado
    for i in I:
        for t in T:
            M = max(0.0, min(float(inst.capacity[t]) - float(inst.setup_time[i]), _rem(inst, i, t)))
            enlace.append(({_x(i, t): 1.0, _y(i, t): -M}, "<=", 0.0))
    # Desigualdades (l,S) con S = intervalo [t, l]
    for i in I:
        for l in range(nT):
            for t in range(l + 1):
                c = {_s(i, l): -1.0}
                for k in range(t, l + 1):
                    c[_x(i, k)] = c.get(_x(i, k), 0.0) + 1.0
                    D = _rem(inst, i, k, l)
                    if D != 0.0:
                        c[_y(i, k)] = c.get(_y(i, k), 0.0) - D
                ls.append((c, "<=", 0.0))
    return {"demanda": demanda, "capacidad": capacidad, "enlace": enlace, "enlace.ls": ls}


def objective_terms(inst):
    I, T = range(inst.n_items), range(inst.n_periods)
    setup = {_y(i, t): float(inst.setup_cost[i]) for i in I for t in T}
    inv = {_s(i, t): float(inst.holding_cost[i]) for i in I for t in T}
    return {"setup": (setup, 0.0), "inventario": (inv, 0.0)}


def variable_groups(inst):
    N, T = inst.n_items, inst.n_periods
    order = [_y(i, t) for t in range(T) for i in range(N)]  # período-mayor
    V = len(order)
    g = max(1, min(V // 4, N))
    groups = {}
    for k in range(0, V, g):
        groups[f"g{k // g}"] = order[k:k + g]
    return groups
