from random import Random
from collections import deque

from generated.jobshop_sequences_cycle.model.parts import canonical

COMPONENT = {
    "name": "critical_block_adjacent_swaps",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"max_strength": {"type": "int", "range": [1, 50]}},
}


def _schedule(inst, sol):
    n = inst.n_jobs
    offs = [0] * (n + 1)
    for j in range(n):
        offs[j + 1] = offs[j] + len(inst.routes[j])
    N = offs[n]
    dur = [0] * N
    jpred = [-1] * N
    mpred = [-1] * N
    job_of = [0] * N
    k_of = [0] * N
    succ = [[] for _ in range(N)]
    indeg = [0] * N
    for j in range(n):
        for k in range(len(inst.routes[j])):
            u = offs[j] + k
            dur[u] = inst.proc(j, k)
            job_of[u] = j
            k_of[u] = k
            if k > 0:
                jpred[u] = u - 1
                succ[u - 1].append(u)
                indeg[u] += 1
    for m, seq in enumerate(sol):
        prev = -1
        seen = set()
        for j in seq:
            if j in seen or j < 0 or j >= n:
                return None
            seen.add(j)
            k = inst.op_index(j, m)
            if k is None:
                return None
            u = offs[j] + k
            if prev >= 0:
                mpred[u] = prev
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
        return None
    return dur, jpred, mpred, job_of, k_of, start


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
        if _schedule(inst, new) is not None:
            return new
    m, i = cands[0]
    return _swap(sol, m, i)


class CriticalBlockAdjacentSwaps:
    def __init__(self, problem, max_strength=20):
        self.problem = problem
        self.inst = problem.inst
        self.max_strength = max_strength

    def _critical_pairs(self, sch, rng):
        dur, jpred, mpred, job_of, k_of, start = sch
        N = len(dur)
        if N == 0:
            return []
        mk = max(start[u] + dur[u] for u in range(N))
        ends = [u for u in range(N) if start[u] + dur[u] == mk]
        u = rng.choice(ends)
        path = [u]
        while True:
            preds = [p for p in (jpred[u], mpred[u])
                     if p >= 0 and start[p] + dur[p] == start[u]]
            if not preds:
                break
            u = rng.choice(preds)
            path.append(u)
        path.reverse()
        pairs = []
        for a, b in zip(path, path[1:]):
            if mpred[b] == a:
                m = self.inst.machine(job_of[b], k_of[b])
                pairs.append((m, job_of[a]))
        return pairs

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        k = max(1, min(self.max_strength, int(round(strength))))
        cur = canonical(sol)
        orig = cur
        last = None
        for _ in range(k):
            sch = _schedule(inst, cur)
            if sch is None:
                break
            pairs = self._critical_pairs(sch, rng)
            if last is not None and len(pairs) > 1:
                pairs = [p for p in pairs if p != last] or pairs
            if not pairs:
                break
            m, ja = rng.choice(pairs)
            i = list(cur[m]).index(ja)
            if i + 1 >= len(cur[m]):
                break
            last = (m, cur[m][i + 1])
            cur = _swap(cur, m, i)
        if cur == orig:
            cur = _fallback(inst, orig, rng)
        return cur


def build_component(problem, max_strength=20):
    return CriticalBlockAdjacentSwaps(problem, max_strength=max_strength)
