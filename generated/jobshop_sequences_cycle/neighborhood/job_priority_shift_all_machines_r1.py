from collections import deque

from generated.jobshop_sequences_cycle.model.parts import canonical

COMPONENT = {
    "name": "job_priority_shift_all_machines",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {
        "max_shift": {"type": "int", "range": [1, 5]},
        "only_critical_jobs": {"type": "bool"},
    },
}


def _critical_jobs(inst, sol):
    """Trabajos con alguna operación en el camino crítico; None si no hay plan."""
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
        mprev, cnt = {}, 0
        for m, seq in enumerate(sol):
            if len(set(seq)) != len(seq):
                return None
            prev = None
            for j in seq:
                k = inst.op_index(j, m)
                if k is None:
                    return None
                u = (j, k)
                cnt += 1
                if prev is not None:
                    mprev[u] = prev
                    succ[prev].append(u)
                    indeg[u] += 1
                prev = u
        if cnt != len(dur):
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
        jobs = set()
        u = last_op
        while u is not None:
            jobs.add(u[0])
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
        return jobs
    except Exception:
        return None


class JobPriorityShiftAllMachines:
    """Cambia la prioridad global de un trabajo: en cada máquina que visita, lo mueve d posiciones
    (d<0 adelanta, d>0 atrasa; recortado a los extremos). Movimiento = (j, d). Es un movimiento
    multi-máquina coordinado que los vecindarios de una sola máquina no alcanzan en un paso."""

    def __init__(self, problem, max_shift, only_critical_jobs):
        self.problem = problem
        self.inst = problem.inst
        self.max_shift = max_shift
        self.only_critical_jobs = only_critical_jobs

    def _changes(self, sol, j, d):
        for seq in sol:
            if j in seq:
                p = seq.index(j)
                t = min(len(seq) - 1, max(0, p + d))
                if t != p:
                    return True
        return False

    def _gen(self, sol, jobs):
        out = []
        for j in jobs:
            for a in range(1, self.max_shift + 1):
                for d in (-a, a):
                    if self._changes(sol, j, d):
                        out.append((j, d))
        return out

    def moves(self, sol):
        all_jobs = sorted({j for seq in sol for j in seq})
        jobs = all_jobs
        if self.only_critical_jobs:
            cj = _critical_jobs(self.inst, sol)
            if cj:
                jobs = sorted(cj)
        out = self._gen(sol, jobs)
        if not out and jobs is not all_jobs:
            out = self._gen(sol, all_jobs)
        return out

    def apply(self, sol, m):
        j, d = m
        seqs = []
        for seq in sol:
            s = list(seq)
            if j in s:
                p = s.index(j)
                t = min(len(s) - 1, max(0, p + d))
                if t != p:
                    s.pop(p)
                    s.insert(t, j)
            seqs.append(s)
        return canonical(seqs)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_shift=2, only_critical_jobs=False):
    return JobPriorityShiftAllMachines(problem, int(max_shift), bool(only_critical_jobs))
