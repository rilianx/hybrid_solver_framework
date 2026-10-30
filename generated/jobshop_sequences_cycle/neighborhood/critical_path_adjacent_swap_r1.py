from collections import deque

from generated.jobshop_sequences_cycle.model.parts import canonical

COMPONENT = {
    "name": "critical_path_adjacent_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


def _schedule(inst, sol):
    """Plan semiactivo. Devuelve (start, dur, mprev, mpos, last_op) o None si hay ciclo/estructura rota."""
    try:
        n = inst.n_jobs
        routes = inst.routes
        dur = {}
        succ = {}
        indeg = {}
        for j in range(n):
            for k in range(len(routes[j])):
                u = (j, k)
                dur[u] = inst.proc(j, k)
                succ.setdefault(u, [])
                indeg.setdefault(u, 0)
                if k + 1 < len(routes[j]):
                    succ[u].append((j, k + 1))
                    indeg[(j, k + 1)] = indeg.get((j, k + 1), 0) + 1
        mprev = {}
        mpos = {}
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
        done = 0
        last_op, mk = None, -1
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


class CriticalPathAdjacentSwap:
    """Intercambia dos operaciones consecutivas de una misma máquina que están unidas por un arco
    de máquina del camino crítico. Movimiento = (m, i): swap de posiciones i, i+1 en la máquina m.
    Si no hay plan (ciclo), cae a todos los swaps adyacentes."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def _all_adjacent(self, sol):
        return [(m, i) for m, seq in enumerate(sol) for i in range(len(seq) - 1)]

    def moves(self, sol):
        sched = _schedule(self.inst, sol)
        out = []
        if sched is not None:
            mprev, mpos = sched[2], sched[3]
            path = _critical_path(sched)
            seen = set()
            for a, b in zip(path, path[1:]):
                if mprev.get(b) == a:
                    m, i = mpos[a]
                    if (m, i) not in seen:
                        seen.add((m, i))
                        out.append((m, i))
        if not out:
            out = self._all_adjacent(sol)
        return out

    def apply(self, sol, m):
        mach, i = m
        seqs = [list(s) for s in sol]
        s = seqs[mach]
        s[i], s[i + 1] = s[i + 1], s[i]
        return canonical(seqs)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem):
    return CriticalPathAdjacentSwap(problem)
