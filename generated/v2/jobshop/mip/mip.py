from examples.jobshop.model_parts import jobs_on, schedule


def _xn(m, j, p):
    return f"x_{m}_{j}_{p}"


def _sn(j, k):
    return f"S_{j}_{k}"


def _tn(m, p):
    return f"T_{m}_{p}"


def _H(inst):
    return float(inst.horizon())


def _clean(inst, sol):
    """Secuencias limpias como las interpreta el oráculo + cantidad de basura (repetidos/ajenos/sobrantes)."""
    cleaned = []
    junk = 0
    for m in inst.machines:
        seq = sol[m] if m < len(sol) else ()
        seen = set()
        out = []
        for j in seq:
            j = int(j)
            if j in seen or not 0 <= j < inst.n_jobs or inst.op_index(j, m) is None:
                junk += 1
                continue
            seen.add(j)
            out.append(j)
        cleaned.append(out)
    junk += sum(len(seq) for seq in sol[inst.n_machines:])
    return cleaned, junk


def variables(inst):
    H = _H(inst)
    v = {}
    for m in inst.machines:
        js = jobs_on(inst, m)
        n = len(js)
        for j in js:
            for p in range(n):
                v[_xn(m, j, p)] = (0.0, 1.0, "binary")
        for p in range(n):
            v[_tn(m, p)] = (0.0, H, "continuous")
    for j in inst.jobs:
        for k in range(len(inst.routes[j])):
            v[_sn(j, k)] = (0.0, H, "continuous")
    v["C"] = (0.0, H, "continuous")
    v["junk"] = (0.0, 1e9, "continuous")
    return v


def structural_variables(inst):
    out = []
    for m in inst.machines:
        js = jobs_on(inst, m)
        n = len(js)
        for j in js:
            for p in range(n):
                out.append(_xn(m, j, p))
    return out


def to_assignment(inst, sol):
    cleaned, _ = _clean(inst, sol)
    a = {name: 0.0 for name in structural_variables(inst)}
    for m in inst.machines:
        for p, j in enumerate(cleaned[m]):
            a[_xn(m, j, p)] = 1.0
    return a


def aux_values(inst, sol):
    cleaned, junk = _clean(inst, sol)
    start, makespan, _ = schedule(inst, sol)
    vals = {}
    for j in inst.jobs:
        for k in range(len(inst.routes[j])):
            vals[_sn(j, k)] = float(start[j][k])
    for m in inst.machines:
        n = len(jobs_on(inst, m))
        seq = cleaned[m]
        t = 0.0
        for p in range(n):
            if p < len(seq):
                j = seq[p]
                k = inst.op_index(j, m)
                t = float(start[j][k])
                vals[_tn(m, p)] = t
                t = t + inst.proc(j, k)
            else:
                vals[_tn(m, p)] = t
    vals["C"] = float(makespan)
    vals["junk"] = float(junk)
    return vals


def from_assignment(inst, x):
    seqs = []
    for m in inst.machines:
        js = jobs_on(inst, m)
        n = len(js)
        seq = []
        for p in range(n):
            for j in js:
                if x.get(_xn(m, j, p), 0.0) > 0.5:
                    seq.append(j)
        seqs.append(tuple(int(j) for j in seq))
    return tuple(seqs)


def constraint_families(inst):
    H = _H(inst)
    sec = []
    orden = []
    head = {}
    tail = {}
    for j in inst.jobs:
        r = inst.routes[j]
        tot = sum(p for _, p in r)
        acc = 0
        for k, (_, p) in enumerate(r):
            head[(j, k)] = acc
            tail[(j, k)] = tot - acc - p
            acc += p

    lb = 0
    for m in inst.machines:
        js = jobs_on(inst, m)
        n = len(js)
        if n == 0:
            continue
        lb = max(lb, sum(inst.proc(j, inst.op_index(j, m)) for j in js))
        # secuencia: asignación
        for j in js:
            sec.append(({_xn(m, j, p): 1.0 for p in range(n)}, "==", 1.0))
        for p in range(n):
            sec.append(({_xn(m, j, p): 1.0 for j in js}, "==", 1.0))
        # orden: cadena de posiciones
        for p in range(n - 1):
            c = {_tn(m, p + 1): 1.0, _tn(m, p): -1.0}
            for j in js:
                c[_xn(m, j, p)] = -float(inst.proc(j, inst.op_index(j, m)))
            orden.append((c, ">=", 0.0))
        for p in range(n):
            # enlace posición-operación (big-M)
            for j in js:
                k = inst.op_index(j, m)
                orden.append(({_sn(j, k): 1.0, _tn(m, p): -1.0, _xn(m, j, p): H}, "<=", H))
                orden.append(({_tn(m, p): 1.0, _sn(j, k): -1.0, _xn(m, j, p): H}, "<=", H))
            # cabeza: la posición no empieza antes de la cabeza de la ruta del trabajo
            c = {_tn(m, p): 1.0}
            for j in js:
                hv = head[(j, inst.op_index(j, m))]
                if hv:
                    c[_xn(m, j, p)] = -float(hv)
            orden.append((c, ">=", 0.0))
            # cola: C >= T + p + cola de ruta
            c = {"C": 1.0, _tn(m, p): -1.0}
            for j in js:
                k = inst.op_index(j, m)
                c[_xn(m, j, p)] = -float(inst.proc(j, k) + tail[(j, k)])
            orden.append((c, ">=", 0.0))

    for j in inst.jobs:
        r = inst.routes[j]
        if not r:
            continue
        lb = max(lb, sum(p for _, p in r))
        for k in range(len(r) - 1):
            orden.append(({_sn(j, k + 1): 1.0, _sn(j, k): -1.0}, ">=", float(inst.proc(j, k))))
        last = len(r) - 1
        orden.append(({"C": 1.0, _sn(j, last): -1.0}, ">=", float(inst.proc(j, last))))
    orden.append(({"C": 1.0}, ">=", float(lb)))
    sec.append(({"junk": 1.0}, "==", 0.0))
    return {"secuencia": sec, "orden": orden}


def objective_terms(inst):
    return {"makespan": ({"C": 1.0}, 0.0)}


def variable_groups(inst):
    groups = []
    for m in inst.machines:
        js = jobs_on(inst, m)
        n = len(js)
        g = [_xn(m, j, p) for p in range(n) for j in js]  # ordenado por posición
        if g:
            groups.append(g)
    total = sum(len(g) for g in groups)
    if total == 0:
        return {}
    while True:
        big = max(range(len(groups)), key=lambda i: len(groups[i]))
        if len(groups) >= 4 and len(groups[big]) * 3 <= total:
            break
        if len(groups[big]) <= 1:
            break
        g = groups.pop(big)
        h = len(g) // 2
        groups.append(g[:h])
        groups.append(g[h:])
    return {f"g{i}": g for i, g in enumerate(groups)}
