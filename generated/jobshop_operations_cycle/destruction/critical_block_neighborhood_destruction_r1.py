from random import Random

from generated.jobshop_operations_cycle.model.parts import canonical

COMPONENT = {
    "name": "critical_block_neighborhood_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "max_radius": {"type": "int", "range": [1, 6]},
    },
}


def _schedule(inst, sol):
    n = inst.n_jobs
    nm = inst.n_machines
    ptr = [0] * n
    disp = []
    for j in sol:
        if not isinstance(j, int) or j < 0 or j >= n:
            continue
        k = ptr[j]
        if k >= len(inst.routes[j]):
            continue
        ptr[j] = k + 1
        disp.append((j, k))
    missing = sorted((k, j) for j in range(n) for k in range(ptr[j], len(inst.routes[j])))
    disp += [(j, k) for (k, j) in missing]
    jr = [0] * n
    mr = [0] * nm
    seqs = [[] for _ in range(nm)]
    start, end = {}, {}
    for (j, k) in disp:
        m, p = inst.routes[j][k]
        if 0 <= m < nm:
            st = max(jr[j], mr[m])
            mr[m] = st + p
            seqs[m].append((j, k))
        else:
            st = jr[j]
        start[(j, k)] = st
        end[(j, k)] = st + p
        jr[j] = st + p
    return start, end, seqs


def _free_pair(free, names, m, a, b):
    for v in (f"y_{m}_{a}_{b}", f"y_{m}_{b}_{a}"):
        if v in names:
            free.add(v)


def _fill_random(free, names, target, rng):
    if len(free) >= target:
        return
    rest = sorted(names - free)
    rng.shuffle(rest)
    for v in rest:
        if len(free) >= target:
            break
        free.add(v)
        parts = v.split("_")
        if len(parts) == 4:
            w = f"y_{parts[1]}_{parts[3]}_{parts[2]}"
            if w in names:
                free.add(w)


class CriticalBlockNeighborhoodDestruction:
    """Libera pares de precedencia en torno al camino crítico (por distancia creciente en la máquina)."""

    def __init__(self, problem, inst, max_radius=3):
        self.problem, self.inst = problem, inst
        self.max_radius = max(1, int(max_radius))

    def _critical_path(self, start, end, seqs, pos, rng):
        if not end:
            return []
        cmax = max(end.values())
        lasts = sorted(o for o, e in end.items() if e == cmax)
        o = lasts[rng.randrange(len(lasts))]
        path = [o]
        seen = {o}
        while True:
            j, k = o
            preds = []
            if k > 0 and (j, k - 1) in end and end[(j, k - 1)] == start[o]:
                preds.append((j, k - 1))
            if o in pos:
                m, i = pos[o]
                if i > 0:
                    q = seqs[m][i - 1]
                    if end[q] == start[o]:
                        preds.append(q)
            preds = [q for q in preds if q not in seen]
            if not preds:
                break
            o = preds[rng.randrange(len(preds))]
            seen.add(o)
            path.append(o)
        return path

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        s = canonical(sol)
        assignment = self.problem.to_assignment(s)
        names = set(assignment)
        total = len(names)
        if total == 0:
            return {}, set()
        target = max(1, min(total, int(round(ratio * total))))
        start, end, seqs = _schedule(inst, s)
        pos = {}
        for m, seq in enumerate(seqs):
            for i, o in enumerate(seq):
                pos[o] = (m, i)
        crit = self._critical_path(start, end, seqs, pos, rng)
        crit_set = set(crit)
        free = set()
        for d in range(1, self.max_radius + 1):
            cands = []
            for o in crit:
                if o not in pos:
                    continue
                m, i = pos[o]
                seq = seqs[m]
                for t in (i - d, i + d):
                    if 0 <= t < len(seq):
                        other = seq[t]
                        tag = 0 if other in crit_set else 1
                        cands.append((tag, rng.random(), m, o[0], other[0]))
            cands.sort()
            for (_t, _r, m, a, b) in cands:
                if len(free) >= target:
                    break
                _free_pair(free, names, m, a, b)
            if len(free) >= target:
                break
        _fill_random(free, names, target, rng)
        partial = {v: val for v, val in assignment.items() if v not in free}
        return partial, free


def build_component(problem, max_radius=3, **_ignored):
    return CriticalBlockNeighborhoodDestruction(problem, problem.inst, max_radius=max_radius)
