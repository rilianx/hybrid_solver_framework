COMPONENT = {
    "name": "critical_block_reinsertion",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts", "ProblemModel.inst"],
    "params": {
        "ends_only": {"type": "bool"},
    },
}


def _analyze(inst, sol):
    n = inst.n_jobs
    nm = inst.n_machines
    routes = inst.routes
    ptr = [0] * n
    jr = [0] * n
    mr = [0] * nm
    mlast = [None] * nm
    seqs = [[] for _ in range(nm)]
    start, end, mprev, mpos = {}, {}, {}, {}
    for t in sol:
        if not isinstance(t, int) or t < 0 or t >= n:
            return None
        k = ptr[t]
        if k >= len(routes[t]):
            return None
        m, p = routes[t][k]
        if m < 0 or m >= nm:
            return None
        st = max(jr[t], mr[m])
        fin = st + p
        op = (t, k)
        start[op] = st
        end[op] = fin
        mprev[op] = mlast[m]
        mpos[op] = (m, len(seqs[m]))
        seqs[m].append(t)
        mlast[m] = op
        jr[t] = fin
        mr[m] = fin
        ptr[t] = k + 1
    for j in range(n):
        if ptr[j] != len(routes[j]):
            return None
    if not end:
        return None
    last = max(end, key=lambda o: (end[o], o))
    path = [last]
    cur = last
    while True:
        mp = mprev[cur]
        j, k = cur
        if mp is not None and end[mp] == start[cur]:
            cur = mp
        elif k > 0 and end[(j, k - 1)] == start[cur]:
            cur = (j, k - 1)
        else:
            break
        path.append(cur)
    path.reverse()
    blocks = []
    cur_m = None
    cur_ps = []
    for op in path:
        m, pos = mpos[op]
        if m == cur_m and cur_ps and pos == cur_ps[-1] + 1:
            cur_ps.append(pos)
        else:
            if len(cur_ps) >= 2:
                blocks.append((cur_m, cur_ps))
            cur_m = m
            cur_ps = [pos]
    if len(cur_ps) >= 2:
        blocks.append((cur_m, cur_ps))
    return seqs, blocks


class CriticalBlockReinsertion:
    """Toma una operación de un bloque crítico y la reinserta en otra posición del mismo bloque
    (adelantarla al inicio o atrasarla al final rompe el bloque de golpe).
    Movimiento = ("i", máquina, desde, hasta) o ("t", i) de respaldo sobre la tupla."""

    def __init__(self, problem, ends_only=False):
        self.problem = problem
        self.inst = problem.inst
        self.parts = problem.parts
        self.ends_only = bool(ends_only)

    def _token_moves(self, sol):
        out = [("t", i) for i in range(len(sol) - 1) if sol[i] != sol[i + 1]]
        if not out:
            out = [("t", 0)]
        return out

    def moves(self, sol):
        sol = tuple(sol)
        res = _analyze(self.inst, sol)
        if res is None:
            return self._token_moves(sol)
        seqs, blocks = res
        seen = set()
        out = []
        for m, ps in blocks:
            first, last = ps[0], ps[-1]
            L = len(seqs[m])
            lo = max(0, first - 1)
            hi = min(L - 1, last + 1)
            for u in ps:
                for v in range(lo, hi + 1):
                    if abs(u - v) < 2:
                        continue
                    if self.ends_only and not (v in (first, last) or u in (first, last)):
                        continue
                    mv = ("i", m, u, v)
                    if mv not in seen:
                        seen.add(mv)
                        out.append(mv)
        if not out:
            for m, s in enumerate(seqs):
                for a in range(len(s)):
                    for b in range(len(s)):
                        if abs(a - b) >= 2:
                            out.append(("i", m, a, b))
        if not out:
            out = self._token_moves(sol)
        return out

    def apply(self, sol, m):
        sol = tuple(sol)
        if m[0] == "t":
            i = m[1]
            s = list(sol)
            if 0 <= i < len(s) - 1:
                s[i], s[i + 1] = s[i + 1], s[i]
            return self.parts.canonical(s)
        res = _analyze(self.inst, sol)
        if res is None:
            return self.parts.canonical(sol)
        seqs, _ = res
        _, mach, u, v = m
        if not (0 <= mach < len(seqs)):
            return self.parts.canonical(sol)
        L = len(seqs[mach])
        if not (0 <= u < L and 0 <= v < L) or u == v:
            return self.parts.canonical(sol)
        seqs = [list(s) for s in seqs]
        x = seqs[mach].pop(u)
        seqs[mach].insert(v, x)
        return self.parts.canonical(self.parts.from_answer(self.inst, seqs))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, ends_only=False):
    return CriticalBlockReinsertion(problem, ends_only=ends_only)
