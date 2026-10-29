from functools import lru_cache
from collections import deque
from examples.jobshop.instance import JSSPInstance


def canonical(sol):
    return tuple(tuple(int(x) for x in seq) for seq in sol)


def trivial_solution(inst):
    # Same global job order on every machine: never creates a cycle.
    seqs = []
    for m in inst.machines:
        seqs.append(tuple(j for j in inst.jobs if inst.op_index(j, m) is not None))
    return canonical(seqs)


def random_solution(inst, rng):
    # Random dispatch: always acyclic (feasible), with a random structure.
    nxt = [0] * inst.n_jobs
    seqs = [[] for _ in inst.machines]
    pending = [j for j in inst.jobs if len(inst.routes[j]) > 0]
    while pending:
        i = rng.randrange(len(pending))
        j = pending[i]
        m = inst.machine(j, nxt[j])
        seqs[m].append(j)
        nxt[j] += 1
        if nxt[j] >= len(inst.routes[j]):
            pending[i] = pending[-1]
            pending.pop()
    return canonical(seqs)


def from_answer(inst, answer):
    return canonical(answer)


@lru_cache(maxsize=4096)
def _evaluate(inst, sol):
    n, M = inst.n_jobs, inst.n_machines
    # --- secuencia ---
    sec = 0
    cleaned = []
    for m in range(M):
        expected = {j for j in range(n) if inst.op_index(j, m) is not None}
        seq = sol[m] if m < len(sol) else ()
        seen = set()
        clean = []
        for j in seq:
            if j in expected and j not in seen:
                seen.add(j)
                clean.append(j)
            else:
                sec += 1  # sobra o se repite
        sec += len(expected - seen)  # faltan
        cleaned.append(clean)
    for m in range(M, len(sol)):
        sec += len(sol[m])

    # --- orden: grafo de operaciones ---
    offs = [0] * (n + 1)
    for j in range(n):
        offs[j + 1] = offs[j] + len(inst.routes[j])
    N = offs[n]
    succ = [[] for _ in range(N)]
    indeg = [0] * N
    dur = [0] * N
    for j in range(n):
        for k in range(len(inst.routes[j])):
            u = offs[j] + k
            dur[u] = inst.proc(j, k)
            if k + 1 < len(inst.routes[j]):
                succ[u].append(u + 1)
                indeg[u + 1] += 1
    for m in range(M):
        clean = cleaned[m]
        for a, b in zip(clean, clean[1:]):
            u = offs[a] + inst.op_index(a, m)
            v = offs[b] + inst.op_index(b, m)
            succ[u].append(v)
            indeg[v] += 1
    start = [0] * N
    q = deque(u for u in range(N) if indeg[u] == 0)
    done = 0
    mk = 0
    while q:
        u = q.popleft()
        done += 1
        f = start[u] + dur[u]
        if f > mk:
            mk = f
        for v in succ[u]:
            if f > start[v]:
                start[v] = f
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    orden = N - done
    H = inst.horizon()
    if sec > 0 or orden > 0:
        cost = float(H + 1 + H * (sec + orden))
    else:
        cost = float(mk)
    return float(sec), float(orden), cost


def violations(inst, sol):
    sec, orden, _ = _evaluate(inst, canonical(sol))
    return {"secuencia": sec, "orden": orden}


def cost_terms(inst, sol):
    _, _, cost = _evaluate(inst, canonical(sol))
    return {"makespan": cost}


# ---- vista MIP ----
from functools import lru_cache
from collections import deque


@lru_cache(maxsize=64)
def _mip_struct(inst):
    E = []
    for m in inst.machines:
        E.append(tuple(j for j in inst.jobs if inst.op_index(j, m) is not None))
    return tuple(E)


def _xn(m, j, q):
    return f"x_{m}_{j}_{q}"


def _sn(j, k):
    return f"S_{j}_{k}"


def _tn(m, q):
    return f"T_{m}_{q}"


def variables(inst):
    E = _mip_struct(inst)
    H = float(inst.horizon())
    v = {}
    for m in inst.machines:
        nm = len(E[m])
        for j in E[m]:
            for q in range(nm):
                v[_xn(m, j, q)] = (0.0, 1.0, "binary")
        for q in range(nm):
            v[_tn(m, q)] = (0.0, H, "continuous")
    for j in inst.jobs:
        for k in range(len(inst.routes[j])):
            v[_sn(j, k)] = (0.0, H, "continuous")
    v["C"] = (0.0, 1e12, "continuous")
    v["sec_err"] = (0.0, 1e9, "continuous")
    v["ord_err"] = (0.0, 1e9, "continuous")
    return v


def structural_variables(inst):
    E = _mip_struct(inst)
    out = []
    for m in inst.machines:
        nm = len(E[m])
        for j in E[m]:
            for q in range(nm):
                out.append(_xn(m, j, q))
    return out


@lru_cache(maxsize=2048)
def _mip_point(inst, sol):
    n, M = inst.n_jobs, inst.n_machines
    E = _mip_struct(inst)
    cleaned = []
    for m in range(M):
        expected = set(E[m])
        seq = sol[m] if m < len(sol) else ()
        seen = set()
        clean = []
        for j in seq:
            if j in expected and j not in seen:
                seen.add(j)
                clean.append(j)
        cleaned.append(clean)
    # graph of operations on cleaned sequences
    offs = [0] * (n + 1)
    for j in range(n):
        offs[j + 1] = offs[j] + len(inst.routes[j])
    N = offs[n]
    succ = [[] for _ in range(N)]
    indeg = [0] * N
    dur = [0] * N
    for j in range(n):
        for k in range(len(inst.routes[j])):
            u = offs[j] + k
            dur[u] = inst.proc(j, k)
            if k + 1 < len(inst.routes[j]):
                succ[u].append(u + 1)
                indeg[u + 1] += 1
    for m in range(M):
        cl = cleaned[m]
        for a, b in zip(cl, cl[1:]):
            u = offs[a] + inst.op_index(a, m)
            w = offs[b] + inst.op_index(b, m)
            succ[u].append(w)
            indeg[w] += 1
    start = [0] * N
    q = deque(u for u in range(N) if indeg[u] == 0)
    while q:
        u = q.popleft()
        f = start[u] + dur[u]
        for w in succ[u]:
            if f > start[w]:
                start[w] = f
            indeg[w] -= 1
            if indeg[w] == 0:
                q.append(w)

    x = {}
    for m in range(M):
        nm = len(E[m])
        for j in E[m]:
            for qq in range(nm):
                x[_xn(m, j, qq)] = 0.0
        for qq, j in enumerate(cleaned[m]):
            if qq < nm:
                x[_xn(m, j, qq)] = 1.0

    aux = {}
    for j in range(n):
        for k in range(len(inst.routes[j])):
            aux[_sn(j, k)] = float(start[offs[j] + k])
    for m in range(M):
        nm = len(E[m])
        cl = cleaned[m]
        last_fin = 0.0
        for qq in range(nm):
            if qq < len(cl):
                j = cl[qq]
                k = inst.op_index(j, m)
                s = float(start[offs[j] + k])
                aux[_tn(m, qq)] = s
                last_fin = s + inst.proc(j, k)
            else:
                aux[_tn(m, qq)] = last_fin
    sec, orden, cost = _evaluate(inst, sol)
    aux["C"] = float(cost)
    aux["sec_err"] = float(sec)
    aux["ord_err"] = float(orden)
    return x, aux


def to_assignment(inst, sol):
    x, _ = _mip_point(inst, canonical(sol))
    return dict(x)


def aux_values(inst, sol):
    _, aux = _mip_point(inst, canonical(sol))
    return dict(aux)


def from_assignment(inst, x):
    E = _mip_struct(inst)
    seqs = []
    for m in inst.machines:
        nm = len(E[m])
        seq = []
        used = set()
        for q in range(nm):
            best, bv = None, 0.5
            for j in E[m]:
                if j in used:
                    continue
                val = float(x.get(_xn(m, j, q), 0.0))
                if val > bv:
                    best, bv = j, val
            if best is not None:
                seq.append(best)
                used.add(best)
        seqs.append(tuple(seq))
    return canonical(seqs)


def constraint_families(inst):
    E = _mip_struct(inst)
    H = float(inst.horizon())
    fam = {
        "secuencia.job": [], "secuencia.pos": [], "secuencia.err": [],
        "orden.ruta": [], "orden.maq": [], "orden.link_lo": [], "orden.link_hi": [],
        "orden.makespan": [], "orden.err": [],
    }
    for m in inst.machines:
        nm = len(E[m])
        for j in E[m]:
            fam["secuencia.job"].append(({_xn(m, j, q): 1.0 for q in range(nm)}, "==", 1.0))
        for q in range(nm):
            fam["secuencia.pos"].append(({_xn(m, j, q): 1.0 for j in E[m]}, "==", 1.0))
        for q in range(nm - 1):
            co = {_tn(m, q + 1): 1.0, _tn(m, q): -1.0}
            for j in E[m]:
                k = inst.op_index(j, m)
                co[_xn(m, j, q)] = -float(inst.proc(j, k))
            fam["orden.maq"].append((co, ">=", 0.0))
        for j in E[m]:
            k = inst.op_index(j, m)
            s = _sn(j, k)
            for q in range(nm):
                xv = _xn(m, j, q)
                fam["orden.link_lo"].append(({s: 1.0, _tn(m, q): -1.0, xv: -H}, ">=", -H))
                fam["orden.link_hi"].append(({s: 1.0, _tn(m, q): -1.0, xv: H}, "<=", H))
    fam["secuencia.err"].append(({"sec_err": 1.0}, "==", 0.0))
    for j in inst.jobs:
        L = len(inst.routes[j])
        for k in range(L - 1):
            fam["orden.ruta"].append(({_sn(j, k + 1): 1.0, _sn(j, k): -1.0}, ">=",
                                      float(inst.proc(j, k))))
        if L > 0:
            fam["orden.makespan"].append(({"C": 1.0, _sn(j, L - 1): -1.0}, ">=",
                                          float(inst.proc(j, L - 1))))
    fam["orden.err"].append(({"ord_err": 1.0}, "==", 0.0))
    return {k: v for k, v in fam.items() if v}


def objective_terms(inst):
    return {"makespan": ({"C": 1.0}, 0.0)}


def variable_groups(inst):
    E = _mip_struct(inst)
    total = sum(len(e) * len(e) for e in E)
    maxn = max((len(e) for e in E), default=0)
    best = None
    for c in range(1, max(1, maxn) + 1):
        groups = {}
        for m in inst.machines:
            nm = len(E[m])
            if nm == 0:
                continue
            cc = min(c, nm)
            for q in range(nm):
                key = f"m{m}_b{q * cc // nm}"
                g = groups.setdefault(key, [])
                for j in E[m]:
                    g.append(_xn(m, j, q))
        best = groups
        if len(groups) >= 4 and max(len(g) for g in groups.values()) * 3 <= total:
            return groups
    return best if best is not None else {}
