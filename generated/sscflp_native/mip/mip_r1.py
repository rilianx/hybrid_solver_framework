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
    a = sol[0]
    n, m = inst.n_facilities, inst.n_customers
    x = {_x(i, j): 0.0 for i in inst.facilities for j in inst.customers}
    for j, i in enumerate(a[:m]):
        i = int(i)
        if 0 <= i < n:
            x[_x(i, j)] = 1.0
    return x


def aux_values(inst, sol):
    a = sol[0]
    n, m = inst.n_facilities, inst.n_customers
    used = {int(i) for i in a[:m] if 0 <= int(i) < n}
    return {_y(i): (1.0 if i in used else 0.0) for i in inst.facilities}


def from_assignment(inst, x):
    out = []
    for j in inst.customers:
        chosen = -1
        best = 0.5
        for i in inst.facilities:
            val = x.get(_x(i, j), 0.0)
            if val > best:
                best = val
                chosen = i
        out.append(chosen)
    return canonical([out])


def constraint_families(inst):
    asign = []
    for j in inst.customers:
        asign.append(({_x(i, j): 1.0 for i in inst.facilities}, "==", 1.0))
    cap = []
    for i in inst.facilities:
        coefs = {_x(i, j): float(inst.demand[j]) for j in inst.customers}
        coefs[_y(i)] = -float(inst.capacity[i])
        cap.append((coefs, "<=", 0.0))
    # enlace fuerte x_ij <= y_i (siempre satisfecho en el punto de una solución)
    for i in inst.facilities:
        for j in inst.customers:
            cap.append(({_x(i, j): 1.0, _y(i): -1.0}, "<=", 0.0))
    return {"asignacion": asign, "capacidad": cap}


def objective_terms(inst):
    apertura = {_y(i): float(inst.fixed[i]) for i in inst.facilities}
    transporte = {_x(i, j): float(inst.cost[i][j])
                  for i in inst.facilities for j in inst.customers}
    return {"apertura": (apertura, 0.0), "transporte": (transporte, 0.0)}


def variable_groups(inst):
    m = inst.n_customers
    groups = {}
    if m >= 4:
        for j in inst.customers:
            groups[f"cliente_{j}"] = [_x(i, j) for i in inst.facilities]
    else:
        for i in inst.facilities:
            for j in inst.customers:
                groups[f"par_{i}_{j}"] = [_x(i, j)]
    return groups
