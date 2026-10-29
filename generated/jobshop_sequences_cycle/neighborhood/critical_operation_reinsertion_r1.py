from collections import deque

from generated.jobshop_sequences_cycle.model.parts import canonical

COMPONENT = {
    "name": "critical_operation_reinsertion",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {
        "max_shift": {"type": "int", "range": [1, 100]},
    },
}


def _schedule(inst, sol):
    try:
        n = inst.n_jobs
        routes = inst.routes
        dur, succ, indeg = {}, {}, {}
        for j in range(n):
            for k in range(len(routes[j])):
                u = (j, k)
                dur[u] = inst.proc(j, k)
                succ.setdefault(u, [])
                indeg.setdefault(u, 0)
                if k + 1 < len(routes[j]):
                    succ[u].append((j, k + 1))
                    indeg[(j, k + 1)] = indeg.get((j, k + 1), 0) + 1
        mprev, mpos = {}, {}
        for m, seq in enumerate(sol):
            if len(set(seq)) != len(seq):
                return None
            prev = None
            for i, j in enumerate(seq):
                k = inst.op_index(j, m)
                if k is None:
                    return None
                u = (j, k)
                mpos[u] = (m, i)
                if prev is not None:
                    mprev[u] = prev
                    succ[prev].append(u)
                    indeg[u] += 1
                prev = u
        if len(mpos) != len(dur):
            return None
        start = {u: 0 for u in dur}
        q = deque(u for u in dur if indeg[u] == 0)
        done, last_op, mk = 0, None, -1
        while q:
            u = q.popleft()
            done += 1
            f = start[u] + dur[u]
            if f > mk:
                mk, last_op = f, u
            for v in succ[u]:
                if f > start[v]:
                    start[v] = f
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        if done != len(dur):
            return None
        return start, dur, mprev, mpos, last_op
    except Exception:
        return None


def _critical_path(sched):
    start, dur, mprev, mpos, last_op = sched
    path = []
    u = last_op
    while u is not None:
        path.append(u)
        s = start[u]
        if s == 0:
            break
        nxt = None
        pm = mprev.get(u)
        if pm is not None and start[pm] + dur[pm] == s:
            nxt = pm
        else:
            j, k = u
            if k > 0 and start[(j, k - 1)] + dur[(j, k - 1)] == s:
                nxt = (j, k - 1)
        u = nxt
    path.reverse()
    return path


class CriticalOperationReinsertion:
    """Saca una operación del camino crítico de su máquina y la reinserta en otra posición
    (hasta max_shift lugares). Movimiento = (m, p, t): pop en p, insert en t. Rompe bloques
    críticos llevando la operación delante o detrás del bloque entero."""

    def __init__(self, problem, max_shift):
        self.problem = problem
        self.inst = problem.inst
        self.max_shift = max_shift

    def _ops(self, sol):
        sched = _schedule(self.inst, sol)
        if sched is None:
            return [(m, p) for m, seq in enumerate(sol) for p in range(len(seq))]
        mpos = sched[3]
        seen, out = set(), []
        for u in _critical_path(sched):
            mp = mpos[u]
            if mp not in seen:
                seen.add(mp)
                out.append(mp)
        if not out:
            out = [(m, p) for m, seq in enumerate(sol) for p in range(len(seq))]
        return out

    def moves(self, sol):
        out = []
        for m, p in self._ops(sol):
            L = len(sol[m])
            lo = max(0, p - self.max_shift)
            hi = min(L - 1, p + self.max_shift)
            for t in range(lo, hi + 1):
                if t != p:
                    out.append((m, p, t))
        if not out:
            for m, seq in enumerate(sol):
                for p in range(len(seq)):
                    for t in range(len(seq)):
                        if t != p:
                            out.append((m, p, t))
        return out

    def sample(self, sol, k, rng):
        mv = list(self.moves(sol))
        if k >= len(mv):
            return mv
        return rng.sample(mv, k)

    def apply(self, sol, m):
        mach, p, t = m
        seqs = [list(s) for s in sol]
        s = seqs[mach]
        x = s.pop(p)
        s.insert(t, x)
        return canonical(seqs)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_shift=100):
    return CriticalOperationReinsertion(problem, int(max_shift))
