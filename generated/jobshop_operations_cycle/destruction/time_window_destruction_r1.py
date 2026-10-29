from random import Random

from generated.jobshop_operations_cycle.model.parts import canonical

COMPONENT = {
    "name": "time_window_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "growth": {"type": "float", "range": [1.1, 3.0]},
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
    cmax = 0
    for (j, k) in disp:
        m, p = inst.routes[j][k]
        if 0 <= m < nm:
            st = max(jr[j], mr[m])
            mr[m] = st + p
            seqs[m].append((j, st, st + p))
        else:
            st = jr[j]
        jr[j] = st + p
        cmax = max(cmax, st + p)
    return seqs, cmax


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


class TimeWindowDestruction:
    """Libera las precedencias entre operaciones que se solapan con una ventana de tiempo aleatoria."""

    def __init__(self, problem, inst, growth=1.5):
        self.problem, self.inst = problem, inst
        self.growth = max(1.1, float(growth))

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        s = canonical(sol)
        assignment = self.problem.to_assignment(s)
        names = set(assignment)
        total = len(names)
        if total == 0:
            return {}, set()
        target = max(1, min(total, int(round(ratio * total))))
        seqs, cmax = _schedule(inst, s)
        cands = []
        if cmax > 0:
            center = rng.uniform(0.0, float(cmax))
            w = max(1.0, ratio * cmax)
            for _ in range(60):
                lo, hi = center - w / 2.0, center + w / 2.0
                cands = []
                for m, seq in enumerate(seqs):
                    inside = [(i, j) for i, (j, st, en) in enumerate(seq) if en > lo and st < hi]
                    for x in range(len(inside)):
                        for y in range(x + 1, len(inside)):
                            ia, a = inside[x]
                            ib, b = inside[y]
                            cands.append((ib - ia, rng.random(), m, a, b))
                if 2 * len(cands) >= target or w >= 2.0 * cmax:
                    break
                w *= self.growth
        cands.sort()
        free = set()
        for (_d, _r, m, a, b) in cands:
            if len(free) >= target:
                break
            for v in (f"y_{m}_{a}_{b}", f"y_{m}_{b}_{a}"):
                if v in names:
                    free.add(v)
        _fill_random(free, names, target, rng)
        partial = {v: val for v, val in assignment.items() if v not in free}
        return partial, free


def build_component(problem, growth=1.5, **_ignored):
    return TimeWindowDestruction(problem, problem.inst, growth=growth)
