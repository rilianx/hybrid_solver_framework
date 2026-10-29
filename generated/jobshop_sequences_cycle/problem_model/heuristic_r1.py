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
