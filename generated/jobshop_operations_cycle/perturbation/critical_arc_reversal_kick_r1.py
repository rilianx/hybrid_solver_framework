from random import Random

from generated.jobshop_operations_cycle.model.parts import canonical

COMPONENT = {
    "name": "critical_arc_reversal_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"critical_prob": {"type": "float", "range": [0.0, 1.0]}},
}


def _force_diff(s, rng):
    n = len(s)
    if n < 2:
        return s
    for _ in range(50):
        i, j = rng.randrange(n), rng.randrange(n)
        if s[i] != s[j]:
            s[i], s[j] = s[j], s[i]
            return s
    for i in range(n - 1):
        if s[i] != s[i + 1]:
            s[i], s[i + 1] = s[i + 1], s[i]
            return s
    return s


class CriticalArcReversalKick:
    def __init__(self, inst, critical_prob=0.8):
        self.inst = inst
        self.critical_prob = float(critical_prob)

    def _critical_machine_arcs(self, s, rng):
        inst = self.inst
        nj = inst.n_jobs
        nm = inst.n_machines
        job_ptr = [0] * nj
        job_last = [-1] * nj
        mach_last = [-1] * nm
        info = {}  # pos -> (st, fin, job_pred_pos, mach_pred_pos)
        fin_of = {}
        best_pos, best_fin = -1, -1
        for pos, j in enumerate(s):
            if not isinstance(j, int) or j < 0 or j >= nj:
                continue
            k = job_ptr[j]
            if k >= len(inst.routes[j]):
                continue
            m, p = inst.routes[j][k]
            job_ptr[j] = k + 1
            if m < 0 or m >= nm:
                continue
            jp = job_last[j]
            mp = mach_last[m]
            jr = fin_of[jp] if jp >= 0 else 0
            mr = fin_of[mp] if mp >= 0 else 0
            st = max(jr, mr)
            fin = st + p
            info[pos] = (st, fin, jp, mp)
            fin_of[pos] = fin
            job_last[j] = pos
            mach_last[m] = pos
            if fin > best_fin:
                best_fin, best_pos = fin, pos
        arcs = []
        cur = best_pos
        guard = 0
        while cur >= 0 and guard <= len(s) + 1:
            guard += 1
            st, _fin, jp, mp = info[cur]
            if st <= 0:
                break
            j_ok = jp >= 0 and fin_of[jp] == st
            m_ok = mp >= 0 and fin_of[mp] == st
            if m_ok and (not j_ok or rng.random() < 0.5):
                if s[mp] != s[cur]:
                    arcs.append((mp, cur))
                cur = mp
            elif j_ok:
                cur = jp
            elif m_ok:
                cur = mp
            else:
                break
        return arcs

    def _random_insertion(self, s, rng):
        n = len(s)
        for _ in range(30):
            i, t = rng.randrange(n), rng.randrange(n)
            if i == t:
                continue
            x = s.pop(i)
            s.insert(t, x)
            return s
        return s

    def perturb(self, sol, strength: float, rng: Random):
        base = canonical(sol)
        n = len(base)
        if n < 2:
            return base
        s = list(base)
        k = max(1, int(round(strength)))
        for _ in range(k):
            done = False
            if rng.random() < self.critical_prob:
                arcs = self._critical_machine_arcs(s, rng)
                if arcs:
                    pu, pv = arcs[rng.randrange(len(arcs))]
                    x = s.pop(pv)
                    s.insert(pu, x)
                    done = True
            if not done:
                s = self._random_insertion(s, rng)
        out = canonical(s)
        if out == base:
            out = canonical(_force_diff(s, rng))
        return out


def build_component(problem, critical_prob=0.8):
    return CriticalArcReversalKick(problem.inst, critical_prob=critical_prob)
