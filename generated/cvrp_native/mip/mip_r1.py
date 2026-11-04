import math

from examples.cvrp.model_parts import canonical, violations, cost_terms

_TOL = 1e-9


def _N(inst):
    return len(inst.coords)


def _x(i, j):
    return f"x_{i}_{j}"


def _u(c):
    return f"u_{c}"


_EXTRA = "dist_extra"


def _u_ub(inst):
    return float(inst.capacity) + float(sum(inst.demand)) + 1.0


def _extra_ub(inst):
    N = _N(inst)
    md = 0.0
    for i in range(N):
        for j in range(i + 1, N):
            md = max(md, inst.dist(i, j))
    return float(max(1e6, 10.0 * N * N * (md + 1.0)))


def _arcs(inst):
    N = _N(inst)
    return [(i, j) for i in range(N) for j in range(N) if i != j]


def variables(inst):
    v = {}
    for i, j in _arcs(inst):
        v[_x(i, j)] = (0.0, 1.0, "binary")
    ub = _u_ub(inst)
    for c in inst.customers:
        v[_u(c)] = (float(inst.demand[c]), ub, "continuous")
    v[_EXTRA] = (0.0, _extra_ub(inst), "continuous")
    return v


def structural_variables(inst):
    return [_x(i, j) for i, j in _arcs(inst)]


def _flags(inst, sol):
    viol = violations(inst, sol)
    return viol.get("visita", 0.0) > _TOL, viol.get("capacidad", 0.0) > _TOL


def to_assignment(inst, sol):
    x = {_x(i, j): 0.0 for i, j in _arcs(inst)}
    V, _ = _flags(inst, sol)
    if not V:
        for r in sol:
            nodes = (0, *r, 0)
            for a, b in zip(nodes, nodes[1:]):
                if a != b and _x(a, b) in x:
                    x[_x(a, b)] = 1.0
    return x


def aux_values(inst, sol):
    V, C = _flags(inst, sol)
    x = to_assignment(inst, sol)
    Q = float(inst.capacity)
    d = inst.demand
    u = {}
    if not V:
        for r in sol:
            load = 0.0
            for c in r:
                load += d[c]
                u[c] = load
    for c in inst.customers:
        if c not in u:
            u[c] = float(d[c])
    if C:
        violated = False
        for c in inst.customers:
            out_load = sum(d[j] * x[_x(c, j)] for j in inst.customers if j != c)
            if u[c] + out_load > Q + 1e-6:
                violated = True
                break
        if not violated and inst.n_customers >= 1:
            u[1] = _u_ub(inst)
    vals = {_u(c): float(u[c]) for c in inst.customers}
    total = cost_terms(inst, sol)["distancia"]
    lin = sum(inst.dist(i, j) * x[_x(i, j)] for i, j in _arcs(inst))
    vals[_EXTRA] = float(max(0.0, total - lin))
    return vals


def from_assignment(inst, x):
    N = _N(inst)
    succ = {}
    for i in range(N):
        for j in range(N):
            if i != j and x.get(_x(i, j), 0.0) > 0.5 and i != 0:
                if i not in succ:
                    succ[i] = j
    routes = []
    used = set()
    for j in range(1, N):
        if x.get(_x(0, j), 0.0) > 0.5 and j not in used:
            route = []
            cur = j
            while cur != 0 and cur is not None and cur not in used:
                route.append(cur)
                used.add(cur)
                cur = succ.get(cur)
            if route:
                routes.append(tuple(route))
    return canonical(routes)


def constraint_families(inst):
    N = _N(inst)
    cust = list(inst.customers)
    n = len(cust)
    d = inst.demand
    Q = float(inst.capacity)

    visita = []
    for c in cust:
        visita.append(({_x(c, j): 1.0 for j in range(N) if j != c}, "==", 1.0))
        visita.append(({_x(j, c): 1.0 for j in range(N) if j != c}, "==", 1.0))

    cap = []
    for c in cust:
        # carga al llegar a c incluye al menos la demanda del predecesor
        coef = {_u(c): 1.0}
        for j in cust:
            if j != c and d[j] > 0:
                coef[_x(j, c)] = -float(d[j])
        cap.append((coef, ">=", float(d[c])))
        # carga en c deja espacio para el sucesor (implica u_c <= Q)
        coef = {_u(c): 1.0}
        for j in cust:
            if j != c and d[j] > 0:
                coef[_x(c, j)] = float(d[j])
        cap.append((coef, "<=", Q))
    # MTZ con lifting de Desrochers-Laporte
    for i in cust:
        for j in cust:
            if i == j:
                continue
            coef = {_u(i): 1.0, _u(j): -1.0, _x(i, j): Q}
            lift = Q - d[i] - d[j]
            if lift > 0:
                coef[_x(j, i)] = float(lift)
            cap.append((coef, "<=", Q - float(d[j])))
    # cota de flota redondeada (escalada por n): n * rutas >= k_min * sum(grados de entrada)
    if n >= 1:
        tot = float(sum(d[c] for c in cust))
        k_min = max(1, int(math.ceil(tot / Q - 1e-9))) if Q > 0 else 1
        coef = {}
        for j in cust:
            coef[_x(0, j)] = coef.get(_x(0, j), 0.0) + float(n)
        for c in cust:
            for j in range(N):
                if j != c:
                    coef[_x(j, c)] = coef.get(_x(j, c), 0.0) - float(k_min)
        coef = {k: v for k, v in coef.items() if v != 0.0}
        cap.append((coef, ">=", 0.0))

    return {"visita": visita, "capacidad": cap}


def objective_terms(inst):
    coef = {_x(i, j): float(inst.dist(i, j)) for i, j in _arcs(inst)}
    coef[_EXTRA] = 1.0
    return {"distancia": (coef, 0.0)}


def variable_groups(inst):
    N = _N(inst)
    cust = list(inst.customers)
    n = len(cust)
    if n >= 4:
        x0, y0 = inst.coords[0]
        order = sorted(cust, key=lambda c: (math.atan2(inst.coords[c][1] - y0, inst.coords[c][0] - x0), c))
        K = max(4, int(math.ceil(n / 4.0)))
        while int(math.ceil(n / K)) > n / 3.0 and K < n:
            K += 1
        groups = {}
        for k in range(K):
            members = order[k * n // K:(k + 1) * n // K]
            names = []
            for i in members:
                names.extend(_x(i, j) for j in range(N) if j != i)
                names.append(_x(0, i))
            if names:
                groups[f"sector_{k}"] = names
        return groups
    if n == 3:
        return {f"desde_{i}": [_x(i, j) for j in range(N) if j != i] for i in range(N)}
    allv = structural_variables(inst)
    K = min(4, len(allv))
    groups = {}
    for k in range(K):
        part = allv[k * len(allv) // K:(k + 1) * len(allv) // K]
        if part:
            groups[f"bloque_{k}"] = part
    return groups
