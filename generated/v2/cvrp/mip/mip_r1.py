import math

from examples.cvrp.model_parts import canonical, cost_terms

_BIG = 1e9


def _xn(i, j):
    return f"x_{i}_{j}"


def _un(c):
    return f"u_{c}"


def _arcs(inst):
    N = inst.n_customers + 1
    return [(i, j) for i in range(N) for j in range(N) if i != j]


def _total_demand(inst):
    return float(sum(inst.demand[c] for c in inst.customers))


def _reduced_routes(inst, sol):
    """Rutas con solo la primera aparición de cada cliente válido (estructura de caminos simples)."""
    n = inst.n_customers
    seen = set()
    routes = []
    for r in sol:
        rr = []
        for c in r:
            try:
                c = int(c)
            except Exception:
                continue
            if 1 <= c <= n and c not in seen:
                seen.add(c)
                rr.append(c)
        if rr:
            routes.append(rr)
    return routes


def variables(inst):
    Q = float(inst.capacity)
    D = _total_demand(inst)
    v = {}
    for i, j in _arcs(inst):
        v[_xn(i, j)] = (0.0, 1.0, "binary")
    for c in inst.customers:
        v[_un(c)] = (float(inst.demand[c]), D + Q, "continuous")
    v["visitas_extra"] = (0.0, _BIG, "continuous")
    v["dist_extra"] = (-_BIG, _BIG, "continuous")
    return v


def structural_variables(inst):
    return [_xn(i, j) for i, j in _arcs(inst)]


def to_assignment(inst, sol):
    x = {_xn(i, j): 0.0 for i, j in _arcs(inst)}
    for r in _reduced_routes(inst, sol):
        nodes = (0, *r, 0)
        for a, b in zip(nodes, nodes[1:]):
            x[_xn(a, b)] = 1.0
    return x


def aux_values(inst, sol):
    n = inst.n_customers
    Q = float(inst.capacity)
    D = _total_demand(inst)
    vals = {}
    # cargas acumuladas sobre la estructura reducida
    for c in inst.customers:
        vals[_un(c)] = float(inst.demand[c])
    red = _reduced_routes(inst, sol)
    for r in red:
        load = 0.0
        for c in r:
            load += inst.demand[c]
            vals[_un(c)] = load
    # sobrecarga real (según las rutas originales)
    overloaded = False
    for r in sol:
        load = 0.0
        for c in r:
            try:
                ci = int(c)
            except Exception:
                continue
            if 0 <= ci <= n:
                load += inst.demand[ci]
        if load - Q > 1e-9:
            overloaded = True
    if overloaded and n >= 1:
        vals[_un(1)] = D + Q
    # visitas repetidas / inválidas
    counts = {}
    invalid = 0
    for r in sol:
        for c in r:
            try:
                ci = int(c)
            except Exception:
                invalid += 1
                continue
            if 1 <= ci <= n:
                counts[ci] = counts.get(ci, 0) + 1
            else:
                invalid += 1
    extra = sum(max(0, k - 1) for k in counts.values()) + invalid
    vals["visitas_extra"] = float(extra)
    valid = extra == 0 and all(counts.get(c, 0) == 1 for c in inst.customers)
    if valid:
        vals["dist_extra"] = 0.0
    else:
        try:
            true_d = cost_terms(inst, sol)["distancia"]
        except Exception:
            true_d = 0.0
        red_d = 0.0
        for r in red:
            nodes = (0, *r, 0)
            red_d += sum(inst.dist(a, b) for a, b in zip(nodes, nodes[1:]))
        vals["dist_extra"] = float(true_d - red_d)
    return vals


def from_assignment(inst, x):
    n = inst.n_customers
    succ = {}
    for i, j in _arcs(inst):
        if x.get(_xn(i, j), 0.0) > 0.5:
            succ.setdefault(i, []).append(j)
    routes = []
    visited = set()
    for j in sorted(succ.get(0, [])):
        if j in visited:
            continue
        r = []
        cur = j
        while cur != 0 and cur not in visited and 1 <= cur <= n:
            visited.add(cur)
            r.append(cur)
            nx = succ.get(cur, [])
            if not nx:
                break
            cur = nx[0]
        if r:
            routes.append(tuple(r))
    return canonical(routes)


def constraint_families(inst):
    Q = float(inst.capacity)
    d = inst.demand
    custs = list(inst.customers)
    N = inst.n_customers + 1

    visita = []
    for c in custs:
        visita.append(({_xn(i, c): 1.0 for i in range(N) if i != c}, "==", 1.0))
        visita.append(({_xn(c, j): 1.0 for j in range(N) if j != c}, "==", 1.0))
    visita.append(({"visitas_extra": 1.0}, "==", 0.0))
    visita.append(({"dist_extra": 1.0}, "==", 0.0))

    cap = []
    for c in custs:
        # cota inferior levantada: u_c >= d_c + sum_j d_j x_jc
        coefs = {_un(c): 1.0}
        for j in custs:
            if j != c and d[j] != 0:
                coefs[_xn(j, c)] = -float(d[j])
        cap.append((coefs, ">=", float(d[c])))
        # cota superior levantada: u_c + sum_j d_j x_cj <= Q
        coefs = {_un(c): 1.0}
        for j in custs:
            if j != c and d[j] != 0:
                coefs[_xn(c, j)] = float(d[j])
        cap.append((coefs, "<=", Q))
        # si c es el primero de la ruta, u_c = d_c
        coefs = {_un(c): 1.0}
        if Q - d[c] != 0:
            coefs[_xn(0, c)] = Q - float(d[c])
        cap.append((coefs, "<=", Q))
    for i in custs:
        for j in custs:
            if i == j:
                continue
            # MTZ levantada (Desrochers-Laporte / Kara)
            coefs = {_un(i): 1.0, _un(j): -1.0, _xn(i, j): Q}
            lift = Q - float(d[i]) - float(d[j])
            if lift != 0:
                coefs[_xn(j, i)] = lift
            cap.append((coefs, "<=", Q - float(d[j])))
            # arcos imposibles por capacidad
            if float(d[i]) + float(d[j]) > Q + 1e-9:
                cap.append(({_xn(i, j): 1.0}, "<=", 0.0))
    return {"visita": visita, "capacidad": cap}


def objective_terms(inst):
    coefs = {_xn(i, j): float(inst.dist(i, j)) for i, j in _arcs(inst)}
    coefs["dist_extra"] = 1.0
    return {"distancia": (coefs, 0.0)}


def variable_groups(inst):
    n = inst.n_customers
    names = structural_variables(inst)
    if n < 4:
        k = min(4, len(names))
        groups = {f"g{g}": [] for g in range(k)}
        for idx, v in enumerate(names):
            groups[f"g{idx % k}"].append(v)
        return {g: vs for g, vs in groups.items() if vs}
    x0, y0 = inst.coords[0]
    custs = sorted(inst.customers,
                   key=lambda c: (math.atan2(inst.coords[c][1] - y0, inst.coords[c][0] - x0), c))
    s = max(1, min(8, n // 4))
    groups = {}
    N = n + 1
    for gi, start in enumerate(range(0, n, s)):
        chunk = custs[start:start + s]
        vs = []
        for c in chunk:
            vs.append(_xn(0, c))
            for j in range(N):
                if j != c:
                    vs.append(_xn(c, j))
        groups[f"sector_{gi}"] = vs
    return groups
