from random import Random

from generated.jobshop_operations_cycle.model.parts import canonical

COMPONENT = {
    "name": "related_jobs_shaw_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "determinism": {"type": "float", "range": [1.0, 10.0]},
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
    start_jm = [dict() for _ in range(n)]
    cmax = 0
    for (j, k) in disp:
        m, p = inst.routes[j][k]
        if 0 <= m < nm:
            st = max(jr[j], mr[m])
            mr[m] = st + p
            start_jm[j][m] = st
        else:
            st = jr[j]
        jr[j] = st + p
        cmax = max(cmax, st + p)
    return start_jm, cmax


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


class RelatedJobsShawDestruction:
    """Shaw-removal sobre trabajos: libera las precedencias entre trabajos relacionados."""

    def __init__(self, problem, inst, determinism=4.0):
        self.problem, self.inst = problem, inst
        self.determinism = max(1.0, float(determinism))

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        s = canonical(sol)
        assignment = self.problem.to_assignment(s)
        names = set(assignment)
        total = len(names)
        if total == 0:
            return {}, set()
        target = max(1, min(total, int(round(ratio * total))))
        start_jm, cmax = _schedule(inst, s)
        n = inst.n_jobs
        max_ops = max(1, max((len(r) for r in inst.routes), default=1))
        scale = float(cmax + 1)

        def rel(a, b):
            shared = [m for m in start_jm[a] if m in start_jm[b]]
            if not shared:
                return 10.0
            diff = sum(abs(start_jm[a][m] - start_jm[b][m]) for m in shared) / len(shared)
            return diff / scale + (1.0 - len(shared) / max_ops)

        free = set()
        if n > 0:
            seed = rng.randrange(n)
            chosen = [seed]
            unchosen = set(range(n)) - {seed}
            while len(free) < target and unchosen:
                r = chosen[rng.randrange(len(chosen))]
                ranked = sorted(unchosen, key=lambda l: (rel(r, l), l))
                idx = int(len(ranked) * (rng.random() ** self.determinism))
                idx = min(idx, len(ranked) - 1)
                l = ranked[idx]
                unchosen.discard(l)
                for c in chosen:
                    for m in start_jm[l]:
                        if m in start_jm[c]:
                            for v in (f"y_{m}_{l}_{c}", f"y_{m}_{c}_{l}"):
                                if v in names:
                                    free.add(v)
                chosen.append(l)
        _fill_random(free, names, target, rng)
        partial = {v: val for v, val in assignment.items() if v not in free}
        return partial, free


def build_component(problem, determinism=4.0, **_ignored):
    return RelatedJobsShawDestruction(problem, problem.inst, determinism=determinism)
