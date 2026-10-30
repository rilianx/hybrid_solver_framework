from random import Random
from collections import deque

from generated.jobshop_sequences_cycle.model.parts import canonical

COMPONENT = {
    "name": "noisy_start_key_redispatch",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "noise_scale": {"type": "float", "range": [0.1, 3.0]},
        "job_fraction": {"type": "float", "range": [0.1, 1.0]},
    },
}


def _starts(inst, sol):
    n = inst.n_jobs
    offs = [0] * (n + 1)
    for j in range(n):
        offs[j + 1] = offs[j] + len(inst.routes[j])
    N = offs[n]
    dur = [0] * N
    succ = [[] for _ in range(N)]
    indeg = [0] * N
    for j in range(n):
        for k in range(len(inst.routes[j])):
            u = offs[j] + k
            dur[u] = inst.proc(j, k)
            if k > 0:
                succ[u - 1].append(u)
                indeg[u] += 1
    for m, seq in enumerate(sol):
        prev = -1
        seen = set()
        for j in seq:
            if j in seen or j < 0 or j >= n:
                return offs, None
            seen.add(j)
            k = inst.op_index(j, m)
            if k is None:
                return offs, None
            u = offs[j] + k
            if prev >= 0:
                succ[prev].append(u)
                indeg[u] += 1
            prev = u
    start = [0] * N
    q = deque(u for u in range(N) if indeg[u] == 0)
    cnt = 0
    while q:
        u = q.popleft()
        cnt += 1
        f = start[u] + dur[u]
        for v in succ[u]:
            if f > start[v]:
                start[v] = f
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    if cnt < N:
        return offs, None
    return offs, start


def _acyclic(inst, sol):
    return _starts(inst, sol)[1] is not None


def _swap(sol, m, i):
    seqs = [list(s) for s in sol]
    seqs[m][i], seqs[m][i + 1] = seqs[m][i + 1], seqs[m][i]
    return canonical(seqs)


def _fallback(inst, sol, rng):
    cands = [(m, i) for m, s in enumerate(sol) for i in range(len(s) - 1)]
    if not cands:
        return sol
    rng.shuffle(cands)
    for m, i in cands:
        new = _swap(sol, m, i)
        if _acyclic(inst, new):
            return new
    m, i = cands[0]
    return _swap(sol, m, i)


class NoisyStartKeyRedispatch:
    def __init__(self, problem, noise_scale=1.0, job_fraction=0.4):
        self.problem = problem
        self.inst = problem.inst
        self.noise_scale = noise_scale
        self.job_fraction = job_fraction
        inst = self.inst
        tot, cnt = 0, 0
        for j in range(inst.n_jobs):
            for k in range(len(inst.routes[j])):
                tot += inst.proc(j, k)
                cnt += 1
        self.avg_p = (tot / cnt) if cnt else 1.0

    def _dispatch(self, offs, key):
        inst = self.inst
        n = inst.n_jobs
        nxt = [0] * n
        seqs = [[] for _ in range(inst.n_machines)]
        pending = [j for j in range(n) if len(inst.routes[j]) > 0]
        while pending:
            best_i, best_k = 0, None
            for i, j in enumerate(pending):
                kv = (key[offs[j] + nxt[j]], j)
                if best_k is None or kv < best_k:
                    best_k, best_i = kv, i
            j = pending[best_i]
            m = inst.machine(j, nxt[j])
            seqs[m].append(j)
            nxt[j] += 1
            if nxt[j] >= len(inst.routes[j]):
                pending.pop(best_i)
        return canonical(seqs)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        orig = canonical(sol)
        offs, start = _starts(inst, orig)
        n = inst.n_jobs
        N = offs[n]
        s = max(1.0, float(strength))
        jobs = [j for j in range(n) if len(inst.routes[j]) > 0]
        if not jobs:
            return orig
        for attempt in range(6):
            amp = self.noise_scale * s * self.avg_p * (1.5 ** attempt)
            if start is None:
                key = [rng.random() for _ in range(N)]
            else:
                key = [float(x) for x in start]
                cnt = max(1, int(round(self.job_fraction * len(jobs))))
                cnt = min(len(jobs), cnt + attempt)
                for j in rng.sample(jobs, cnt):
                    shift = rng.uniform(-amp, amp)
                    for k in range(len(inst.routes[j])):
                        key[offs[j] + k] += shift + rng.gauss(0.0, 0.25 * amp)
            new = self._dispatch(offs, key)
            if new != orig:
                return new
        return _fallback(inst, orig, rng)


def build_component(problem, noise_scale=1.0, job_fraction=0.4):
    return NoisyStartKeyRedispatch(problem, noise_scale=noise_scale, job_fraction=job_fraction)
