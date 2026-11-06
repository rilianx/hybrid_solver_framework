import math

from examples.sscflp.model_parts import canonical


def _x(i, j):
    return f"x_{i}_{j}"


def _y(i):
    return f"y_{i}"


def variables(inst):
    v = {}
    for i in inst.facilities:
        for j in inst.customers:
            v[_x(i, j)] = (0.0, 1.0, "binary")
    for i in inst.facilities:
        v[_y(i)] = (0.0, 1.0, "binary")
    return v


def structural_variables(inst):
    return [_x(i, j) for i in inst.facilities for j in inst.customers]


def to_assignment(inst, sol):
    n, m = inst.n_facilities, inst.n_customers
    s = list(sol[0])[:m]
    a = {_x(i, j): 0.0 for i in range(n) for j in range(m)}
    for j, i in enumerate(s):
        i = int(i)
        if 0 <= i < n:
            a[_x(i, j)] = 1.0
    return a


def aux_values(inst, sol):
    n, m = inst.n_facilities, inst.n_customers
    s = list(sol[0])[:m]
    used = {int(i) for i in s if 0 <= int(i) < n}
    return {_y(i): (1.0 if i in used else 0.0) for i in range(n)}


def from_assignment(inst, x):
    res = []
    for j in inst.customers:
        best, bv = -1, 0.5
        for i in inst.facilities:
            val = x.get(_x(i, j), 0.0)
            if val > bv:
                best, bv = i, val
        res.append(best)
    return canonical([res])


def constraint_families(inst):
    asign = []
    for j in inst.customers:
        asign.append(({_x(i, j): 1.0 for i in inst.facilities}, "==", 1.0))
    carga = []
    for i in inst.facilities:
        coefs = {}
        for j in inst.customers:
            d = float(inst.demand[j])
            if d != 0.0:
                coefs[_x(i, j)] = d
        coefs[_y(i)] = -float(inst.capacity[i])
        carga.append((coefs, "<=", 0.0))
    enlace = []
    for i in inst.facilities:
        for j in inst.customers:
            enlace.append(({_x(i, j): 1.0, _y(i): -1.0}, "<=", 0.0))
    return {
        "asignacion": asign,
        "capacidad.carga": carga,
        "capacidad.enlace": enlace,
    }


def objective_terms(inst):
    apertura = {_y(i): float(inst.fixed[i]) for i in inst.facilities}
    transporte = {_x(i, j): float(inst.cost[i][j])
                  for i in inst.facilities for j in inst.customers}
    return {"apertura": (apertura, 0.0), "transporte": (transporte, 0.0)}


def _balanced_chunks(items, k):
    L = len(items)
    k = max(1, min(k, L))
    base, extra = divmod(L, k)
    out, pos = [], 0
    for c in range(k):
        size = base + (1 if c < extra else 0)
        out.append(items[pos:pos + size])
        pos += size
    return [c for c in out if c]


def variable_groups(inst):
    n, m = inst.n_facilities, inst.n_customers
    if m >= 4:
        # clientes cercanos (mismo centro más barato) juntos
        def key(j):
            best = min(inst.facilities, key=lambda i: (inst.cost[i][j], i))
            return (best, inst.cost[best][j], j)
        order = sorted(inst.customers, key=key)
        k = max(4, math.ceil(m / 8))
        k = min(k, m)
        while k < m and math.ceil(m / k) > m / 3.0:
            k += 1
        chunks = _balanced_chunks(order, k)
        groups = {}
        for g, ch in enumerate(chunks):
            groups[f"clientes_{g}"] = [_x(i, j) for j in ch for i in inst.facilities]
        return groups
    # pocos clientes: partición balanceada de las variables
    allv = [_x(i, j) for j in inst.customers for i in inst.facilities]
    L = len(allv)
    k = max(4, 3)
    k = min(L, k)
    while k < L and math.ceil(L / k) > L / 3.0:
        k += 1
    chunks = _balanced_chunks(allv, k)
    return {f"bloque_{g}": ch for g, ch in enumerate(chunks)}
