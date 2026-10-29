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
    # secuencias filtradas: trabajos válidos, que pasan por la máquina, sin repetir
    seqs = []
    for m in inst.machines:
        lst = list(answer[m]) if m < len(answer) else []
        seen = set()
        s = []
        for j in lst:
            try:
                j = int(j)
            except Exception:
                continue
            if j < 0 or j >= n or j in seen:
                continue
            if inst.op_index(j, m) is None:
                continue
            seen.add(j)
            s.append(j)
        seqs.append(s)
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
    # operaciones no agendables (faltan o ciclo) se omiten -> violación de secuencia
    return tuple(j for _, j, _ in scheduled)


@lru_cache(maxsize=4096)
def _decode(inst, sol):
    n = inst.n_jobs
    job_ptr = [0] * n
    job_ready = [0] * n
    mach_ready = [0] * inst.n_machines
    extra = 0
    makespan = 0
    for j in sol:
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
    return float(extra + missing), 0.0, float(makespan)


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
