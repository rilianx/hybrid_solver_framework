from examples.jobshop.model_parts import jobs_on, schedule


def _xn(m, j, q):
    return f"x_m{m}_j{j}_q{q}"


def _sn(j, k):
    return f"s_j{j}_k{k}"


def _hn(m, q):
    return f"h_m{m}_q{q}"


def _head_tail(inst):
    head, tail = {}, {}
    for j in inst.jobs:
        r = inst.routes[j]
        acc = 0
        for k in range(len(r)):
            head[(j, k)] = acc
            acc += r[k][1]
        acc = 0
        for k in range(len(r) - 1, -1, -1):
            tail[(j, k)] = acc
            acc += r[k][1]
    return head, tail


def _filtered(inst, sol):
    """Primera aparición válida de cada trabajo en cada máquina, y cantidad de basura."""
    seqs, junk = [], 0
    for m in inst.machines:
        seq = sol[m] if m < len(sol) else ()
        seen, lst = set(), []
        for j in seq:
            j = int(j)
            if 0 <= j < inst.n_jobs and inst.op_index(j, m) is not None and j not in seen:
                seen.add(j)
                lst.append(j)
            else:
                junk += 1
        seqs.append(lst)
    junk += sum(len(seq) for seq in sol[inst.n_machines:])
    return seqs, junk


def variables(inst):
    H = float(inst.horizon())
    head, tail = _head_tail(inst)
    v = {}
    for m in inst.machines:
        J = jobs_on(inst, m)
        n = len(J)
        for j in J:
            for q in range(n):
                v[_xn(m, j, q)] = (0.0, 1.0, "binary")
    for j in inst.jobs:
        for k in range(len(inst.routes[j])):
            p = inst.proc(j, k)
            v[_sn(j, k)] = (float(head[(j, k)]), float(H - tail[(j, k)] - p), "continuous")
    for m in inst.machines:
        n = len(jobs_on(inst, m))
        for q in range(n):
            v[_hn(m, q)] = (0.0, H, "continuous")
    lbc = float(max((sum(p for _, p in r) for r in inst.routes), default=0))
    v["Cmax"] = (lbc, max(H, lbc), "continuous")
    v["extra"] = (0.0, 1e9, "continuous")
    return v


def structural_variables(inst):
    out = []
    for m in inst.machines:
        J = jobs_on(inst, m)
        n = len(J)
        for j in J:
            for q in range(n):
                out.append(_xn(m, j, q))
    return out


def to_assignment(inst, sol):
    x = {name: 0.0 for name in structural_variables(inst)}
    seqs, _ = _filtered(inst, sol)
    for m in inst.machines:
        for q, j in enumerate(seqs[m]):
            x[_xn(m, j, q)] = 1.0
    return x


def aux_values(inst, sol):
    seqs, junk = _filtered(inst, sol)
    start, makespan, _ = schedule(inst, sol)
    a = {}
    for j in inst.jobs:
        for k in range(len(inst.routes[j])):
            a[_sn(j, k)] = float(start[j][k])
    for m in inst.machines:
        n = len(jobs_on(inst, m))
        lst = seqs[m]
        L = len(lst)
        if L > 0:
            lj = lst[-1]
            lk = inst.op_index(lj, m)
            last_end = float(start[lj][lk] + inst.proc(lj, lk))
        else:
            last_end = 0.0
        for q in range(n):
            if q < L:
                j = lst[q]
                a[_hn(m, q)] = float(start[j][inst.op_index(j, m)])
            else:
                a[_hn(m, q)] = last_end
    a["Cmax"] = float(makespan)
    a["extra"] = float(junk)
    return a


def from_assignment(inst, x):
    seqs = []
    for m in inst.machines:
        J = jobs_on(inst, m)
        n = len(J)
        seq = []
        for q in range(n):
            best, bv = None, 0.5
            for j in J:
                val = x.get(_xn(m, j, q), 0.0)
                if val > bv:
                    best, bv = j, val
            if best is not None:
                seq.append(best)
        seqs.append(tuple(int(j) for j in seq))
    return tuple(seqs)


def constraint_families(inst):
    H = float(inst.horizon())
    head, tail = _head_tail(inst)
    sec, orden = [], []
    # --- secuencia ---
    for m in inst.machines:
        J = jobs_on(inst, m)
        n = len(J)
        for j in J:
            sec.append(({_xn(m, j, q): 1.0 for q in range(n)}, "==", 1.0))
        for q in range(n):
            sec.append(({_xn(m, j, q): 1.0 for j in J}, "==", 1.0))
    sec.append(({"extra": 1.0}, "==", 0.0))
    # --- orden ---
    for j in inst.jobs:
        r = inst.routes[j]
        for k in range(len(r) - 1):
            orden.append(({_sn(j, k + 1): 1.0, _sn(j, k): -1.0}, ">=", float(r[k][1])))
        if r:
            kl = len(r) - 1
            orden.append(({"Cmax": 1.0, _sn(j, kl): -1.0}, ">=", float(r[kl][1])))
    for m in inst.machines:
        J = jobs_on(inst, m)
        n = len(J)
        kidx = {j: inst.op_index(j, m) for j in J}
        for q in range(n):
            # cadena de posiciones
            if q + 1 < n:
                c = {_hn(m, q + 1): 1.0, _hn(m, q): -1.0}
                for j in J:
                    c[_xn(m, j, q)] = -float(inst.proc(j, kidx[j]))
                orden.append((c, ">=", 0.0))
            # cabeza
            c = {_hn(m, q): 1.0}
            for j in J:
                hd = head[(j, kidx[j])]
                if hd:
                    c[_xn(m, j, q)] = -float(hd)
            orden.append((c, ">=", 0.0))
            # cola
            c = {"Cmax": 1.0, _hn(m, q): -1.0}
            for j in J:
                k = kidx[j]
                c[_xn(m, j, q)] = -float(inst.proc(j, k) + tail[(j, k)])
            orden.append((c, ">=", 0.0))
            # enlace s <-> h
            for j in J:
                k = kidx[j]
                p = inst.proc(j, k)
                ub_s = H - tail[(j, k)] - p
                M1 = float(max(ub_s, 0.0))
                M2 = float(max(H - head[(j, k)], 0.0))
                orden.append(({_sn(j, k): 1.0, _hn(m, q): -1.0, _xn(m, j, q): M1}, "<=", M1))
                orden.append(({_hn(m, q): 1.0, _sn(j, k): -1.0, _xn(m, j, q): M2}, "<=", M2))
    return {"secuencia": sec, "orden": orden}


def objective_terms(inst):
    return {"makespan": ({"Cmax": 1.0}, 0.0)}


def variable_groups(inst):
    struct = structural_variables(inst)
    total = len(struct)
    if total == 0:
        return {}
    if total < 4:
        return {f"g{i}": [v] for i, v in enumerate(struct)}
    info = []
    for m in inst.machines:
        J = jobs_on(inst, m)
        info.append((m, J, len(J)))
    maxn = max((n for _, _, n in info), default=0)
    for c in range(1, maxn + 1):
        groups = {}
        for m, J, n in info:
            if n == 0:
                continue
            for t in range(c):
                qs = range(t * n // c, (t + 1) * n // c)
                names = [_xn(m, j, q) for q in qs for j in J]
                if names:
                    groups[f"m{m}_c{t}"] = names
        if len(groups) >= 4 and max(len(g) for g in groups.values()) <= total / 3.0:
            return groups
    # respaldo: trozos contiguos de tamaño <= total/4
    size = max(1, total // 4)
    groups, i, g = {}, 0, 0
    while i < total:
        groups[f"g{g}"] = struct[i:i + size]
        i += size
        g += 1
    return groups
