from random import Random
from collections import deque

from generated.jobshop_sequences_cycle.model.parts import canonical

COMPONENT = {
    "name": "acyclic_random_insertions",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "max_tries": {"type": "int", "range": [5, 100]},
        "max_shift": {"type": "int", "range": [1, 50]},
    },
}


def _acyclic(inst, sol):
    n = inst.n_jobs
    offs = [0] * (n + 1)
    for j in range(n):
        offs[j + 1] = offs[j] + len(inst.routes[j])
    N = offs[n]
    succ = [[] for _ in range(N)]
    indeg = [0] * N
    for j in range(n):
        for k in range(1, len(inst.routes[j])):
            u = offs[j] + k
            succ[u - 1].append(u)
            indeg[u] += 1
    for m, seq in enumerate(sol):
        prev = -1
        seen = set()
        for j in seq:
            if j in seen or j < 0 or j >= n:
                return False
            seen.add(j)
            k = inst.op_index(j, m)
            if k is None:
                return False
            u = offs[j] + k
            if prev >= 0:
                succ[prev].append(u)
                indeg[u] += 1
            prev = u
    q = deque(u for u in range(N) if indeg[u] == 0)
    cnt = 0
    while q:
        u = q.popleft()
        cnt += 1
        for v in succ[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return cnt == N


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


class AcyclicRandomInsertions:
    def __init__(self, problem, max_tries=30, max_shift=10):
        self.problem = problem
        self.inst = problem.inst
        self.max_tries = max_tries
        self.max_shift = max_shift

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        orig = canonical(sol)
        machines = [m for m, s in enumerate(orig) if len(s) >= 2]
        if not machines:
            return orig
        k = max(1, int(round(strength)))
        cur = orig
        base_ok = _acyclic(inst, orig)
        jobs = sorted({j for s in orig for j in s})
        if not jobs:
            return orig
        for _ in range(k):
            j = rng.choice(jobs)
            ms = [m for m in range(len(cur)) if len(cur[m]) >= 2 and j in cur[m]]
            rng.shuffle(ms)
            for m in ms:
                seq0 = list(cur[m])
                L = len(seq0)
                i = seq0.index(j)
                lo = max(0, i - self.max_shift)
                hi = min(L - 1, i + self.max_shift)
                far = [p for p in range(lo, hi + 1) if abs(p - i) >= 2]
                near = [p for p in range(lo, hi + 1) if abs(p - i) == 1]
                choices = far if far else near
                if not choices:
                    continue
                rng.shuffle(choices)
                for p in choices[: self.max_tries]:
                    seq = list(seq0)
                    x = seq.pop(i)
                    seq.insert(p, x)
                    seqs = [list(s) for s in cur]
                    seqs[m] = seq
                    cand = canonical(seqs)
                    if cand == cur:
                        continue
                    if not base_ok or _acyclic(inst, cand):
                        cur = cand
                        break
        if cur == orig:
            cur = _fallback(inst, orig, rng)
        return cur


def build_component(problem, max_tries=30, max_shift=10):
    return AcyclicRandomInsertions(problem, max_tries=max_tries, max_shift=max_shift)
