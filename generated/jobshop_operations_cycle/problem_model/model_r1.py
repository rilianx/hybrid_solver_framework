from functools import lru_cache
from examples.jobshop.instance import JSSPInstance


def canonical(sol):
    return tuple(int(x) for x in sol)


def trivial_solution(inst):
    out = []
    maxlen = max((len(r) for r in inst.routes), default=0)
    for k in range(maxlen):
        for j in inst.jobs:
            if k < len(inst.routes[j]):
                out.append(j)
    return tuple(out)


def random_solution(inst, rng):
    seq = [j for j in inst.jobs for _ in range(len(inst.routes[j]))]
    rng.shuffle(seq)
    return tuple(seq)


def from_answer(inst, answer):
    n = inst.n_jobs
    structural = False
    try:
        if len(answer) != inst.n_machines:
            structural = True
    except Exception:
        structural = True
        answer = []
    seqs = []
    for m in inst.machines:
        lst = list(answer[m]) if m < len(answer) else []
        seen = set()
        s = []
        for j in lst:
            try:
                j = int(j)
            except Exception:
                structural = True
                continue
            if j < 0 or j >= n or j in seen:
                structural = True
                continue
            if inst.op_index(j, m) is None:
                structural = True
                continue
            seen.add(j)
            s.append(j)
        seqs.append(s)
    # operaciones que faltan en la respuesta -> problema estructural (secuencia)
    for j in inst.jobs:
        for (m, _p) in inst.routes[j]:
            if m < 0 or m >= inst.n_machines or j not in seqs[m]:
                structural = True
    job_ptr = [0] * n
    job_ready = [0] * n
    mach_ptr = [0] * inst.n_machines
    mach_ready = [0] * inst.n_machines
    scheduled = []  # (start, job, k)
    progress = True
    while progress:
        progress = False
        for m in inst.machines:
            while mach_ptr[m] < len(seqs[m]):
                j = seqs[m][mach_ptr[m]]
                k = job_ptr[j]
                if k >= len(inst.routes[j]) or inst.machine(j, k) != m:
                    break
                st = max(job_ready[j], mach_ready[m])
                fin = st + inst.proc(j, k)
                job_ready[j] = fin
                mach_ready[m] = fin
                job_ptr[j] += 1
                mach_ptr[m] += 1
                scheduled.append((st, j, k))
                progress = True
    scheduled.sort()
    out = [j for _, j, _ in scheduled]
    if not structural:
        # bloqueo sin faltantes -> ciclo entre órdenes y rutas: marcador -1 por operación
        blocked = sum(len(inst.routes[j]) - job_ptr[j] for j in range(n))
        out.extend([-1] * blocked)
    return tuple(out)


@lru_cache(maxsize=4096)
def _decode(inst, sol):
    n = inst.n_jobs
    job_ptr = [0] * n
    job_ready = [0] * n
    mach_ready = [0] * inst.n_machines
    extra = 0
    markers = 0
    makespan = 0
    for j in sol:
        if j == -1:
            markers += 1
            continue
        if not isinstance(j, int) or j < 0 or j >= n:
            extra += 1
            continue
        k = job_ptr[j]
        if k >= len(inst.routes[j]):
            extra += 1
            continue
        m, p = inst.routes[j][k]
        if m < 0 or m >= inst.n_machines:
            extra += 1
            job_ptr[j] += 1
            continue
        st = max(job_ready[j], mach_ready[m])
        fin = st + p
        job_ready[j] = fin
        mach_ready[m] = fin
        job_ptr[j] = k + 1
        if fin > makespan:
            makespan = fin
    missing = sum(len(inst.routes[j]) - job_ptr[j] for j in range(n))
    orden = min(markers, missing)
    sec = extra + max(0, missing - markers) + max(0, markers - missing)
    return float(sec), float(orden), float(makespan)


def violations(inst, sol):
    sec, orden, _ = _decode(inst, canonical(sol))
    return {"secuencia": sec, "orden": orden}


def cost_terms(inst, sol):
    sec, orden, mk = _decode(inst, canonical(sol))
    v = sec + orden
    if v > 0:
        h = float(inst.horizon())
        mk = h + 1.0 + h * v + mk
    return {"makespan": float(mk)}


# ---- vista MIP ----
from functools import lru_cache


def _ybn(m, a, b):
    return f"y_{m}_{a}_{b}"


def _sn(j, k):
    return f"s_{j}_{k}"


@lru_cache(maxsize=64)
def _machine_jobs(inst):
    out = []
    for m in inst.machines:
        out.append(tuple(j for j in inst.jobs if inst.op_index(j, m) is not None))
    return tuple(out)


@lru_cache(maxsize=64)
def _pairs(inst):
    # (m, a, b) con a < b, ambos pasan por m
    mj = _machine_jobs(inst)
    res = []
    for m in inst.machines:
        js = mj[m]
        for i in range(len(js)):
            for t in range(i + 1, len(js)):
                res.append((m, js[i], js[t]))
    return tuple(res)


def _bigM(inst):
    return float(max(1, inst.horizon()))


_BIG = 1e9


def variables(inst):
    v = {}
    for (m, a, b) in _pairs(inst):
        v[_ybn(m, a, b)] = (0.0, 1.0, "binary")
        v[_ybn(m, b, a)] = (0.0, 1.0, "binary")
    for j in inst.jobs:
        for k in range(len(inst.routes[j])):
            v[_sn(j, k)] = (0.0, _BIG, "continuous")
    v["Cmax"] = (0.0, _BIG, "continuous")
    v["desajuste"] = (0.0, _BIG, "continuous")
    return v


def structural_variables(inst):
    out = []
    for (m, a, b) in _pairs(inst):
        out.append(_ybn(m, a, b))
        out.append(_ybn(m, b, a))
    return out


@lru_cache(maxsize=2048)
def _mip_point(inst, sol):
    n = inst.n_jobs
    nm = inst.n_machines
    ptr = [0] * n
    disp = []
    for j in sol:
        if not isinstance(j, int) or j < 0 or j >= n:
            continue
        k = ptr[j]
        if k >= len(inst.routes[j]):
            continue
        ptr[j] = k + 1
        disp.append((j, k))
    missing = sorted((k, j) for j in range(n) for k in range(ptr[j], len(inst.routes[j])))
    disp += [(j, k) for (k, j) in missing]
    jr = [0] * n
    mr = [0] * nm
    seqs = [[] for _ in range(nm)]
    start = {}
    for (j, k) in disp:
        m, p = inst.routes[j][k]
        if 0 <= m < nm:
            st = max(jr[j], mr[m])
            mr[m] = st + p
            seqs[m].append(j)
        else:
            st = jr[j]
        start[(j, k)] = float(st)
        jr[j] = st + p
    sec, orden, _ = _decode(inst, sol)
    cmax = float(cost_terms(inst, sol)["makespan"])
    if orden > 0:
        for (k, j) in missing:
            if inst.proc(j, k) > 0:
                start[(j, k)] = cmax
                break
    y = {}
    for m in range(nm):
        pos = {j: i for i, j in enumerate(seqs[m])}
        for jj in _machine_jobs(inst)[m]:
            pos.setdefault(jj, len(pos) + 10 ** 6)
        y[m] = pos
    yv = []
    for (m, a, b) in _pairs(inst):
        ab = 1.0 if y[m][a] < y[m][b] else 0.0
        yv.append((_ybn(m, a, b), ab))
        yv.append((_ybn(m, b, a), 1.0 - ab))
    sv = tuple((_sn(j, k), start[(j, k)]) for (j, k) in sorted(start))
    return tuple(yv), sv, cmax, float(sec)


def to_assignment(inst, sol):
    yv, _, _, _ = _mip_point(inst, canonical(sol))
    return dict(yv)


def aux_values(inst, sol):
    _, sv, cmax, sec = _mip_point(inst, canonical(sol))
    out = dict(sv)
    out["Cmax"] = cmax
    out["desajuste"] = sec
    return out


def from_assignment(inst, x):
    mj = _machine_jobs(inst)
    answer = []
    for m in inst.machines:
        js = mj[m]
        keyed = []
        for a in js:
            preds = 0
            for b in js:
                if b != a and float(x.get(_ybn(m, b, a), 0.0)) > 0.5:
                    preds += 1
            keyed.append((preds, a))
        keyed.sort()
        answer.append([a for _, a in keyed])
    return from_answer(inst, answer)


def constraint_families(inst):
    M = _bigM(inst)
    par = []
    maq = []
    for (m, a, b) in _pairs(inst):
        yab = _ybn(m, a, b)
        yba = _ybn(m, b, a)
        par.append(({yab: 1.0, yba: 1.0}, "==", 1.0))
        ka = inst.op_index(a, m)
        kb = inst.op_index(b, m)
        pa = float(inst.proc(a, ka))
        pb = float(inst.proc(b, kb))
        sa = _sn(a, ka)
        sb = _sn(b, kb)
        # s_b >= s_a + p_a - M(1 - y_ab)
        maq.append(({sb: 1.0, sa: -1.0, yab: -M}, ">=", pa - M))
        # s_a >= s_b + p_b - M(1 - y_ba)
        maq.append(({sa: 1.0, sb: -1.0, yba: -M}, ">=", pb - M))
    ruta = []
    mk = []
    for j in inst.jobs:
        r = inst.routes[j]
        for k in range(len(r) - 1):
            ruta.append(({_sn(j, k + 1): 1.0, _sn(j, k): -1.0}, ">=", float(r[k][1])))
        if r:
            L = len(r) - 1
            mk.append(({"Cmax": 1.0, _sn(j, L): -1.0}, ">=", float(r[L][1])))
    return {
        "secuencia.par": par,
        "secuencia.cuenta": [({"desajuste": 1.0}, "<=", 0.0)],
        "orden.ruta": ruta,
        "orden.maquina": maq,
        "orden.makespan": mk,
    }


def objective_terms(inst):
    return {"makespan": ({"Cmax": 1.0}, 0.0)}


def variable_groups(inst):
    pairs = _pairs(inst)
    U = len(pairs)
    groups = {}
    if U == 0:
        return groups
    if U < 4:
        for i, (m, a, b) in enumerate(pairs):
            groups[f"g{i}"] = [_ybn(m, a, b), _ybn(m, b, a)]
        return groups
    g = max(4, inst.n_machines)
    c = max(1, U // g)
    by_m = {}
    for (m, a, b) in pairs:
        by_m.setdefault(m, []).append((a, b))
    idx = 0
    for m in sorted(by_m):
        lst = by_m[m]
        for s in range(0, len(lst), c):
            chunk = lst[s:s + c]
            names = []
            for (a, b) in chunk:
                names.append(_ybn(m, a, b))
                names.append(_ybn(m, b, a))
            groups[f"m{m}_{idx}"] = names
            idx += 1
    return groups
