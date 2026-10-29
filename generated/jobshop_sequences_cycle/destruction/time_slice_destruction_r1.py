from random import Random

from generated.jobshop_sequences_cycle.model.parts import canonical

COMPONENT = {
    "name": "time_slice_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "parts.aux_values"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
    },
}


def _structure(assign):
    jobs_on, seq = {}, {}
    for name, val in assign.items():
        p = name.split("_")
        if len(p) != 4 or p[0] != "x":
            continue
        m, j, q = int(p[1]), int(p[2]), int(p[3])
        jobs_on.setdefault(m, set()).add(j)
        if val > 0.5:
            seq.setdefault(m, {})[q] = j
    info = {}
    for m, js in jobs_on.items():
        n = len(js)
        info[m] = (sorted(js), [seq.get(m, {}).get(q) for q in range(n)])
    return info


def _free_window(m, info_m, qs, free):
    jobs, s = info_m
    sel = {s[q] for q in qs if s[q] is not None}
    if any(s[q] is None for q in qs):
        placed = {x for x in s if x is not None}
        sel |= set(jobs) - placed
    for j in sel:
        for q in qs:
            free.add(f"x_{m}_{j}_{q}")


class TimeSliceDestruction:
    """Libera, en todas las máquinas, las posiciones cuyo inicio cae en una franja temporal aleatoria."""

    def __init__(self, problem, ratio=0.2):
        self.problem = problem
        self.inst = problem.inst
        self.ratio = ratio

    def destroy(self, sol, ratio: float, rng: Random):
        sol = canonical(sol)
        if ratio is None:
            ratio = self.ratio
        inst = self.inst
        assign = self.problem.to_assignment(sol)
        info = _structure(assign)
        machines = [m for m in info if len(info[m][0]) > 0]
        P = sum(len(info[m][0]) for m in machines)
        target = min(P, max(2, int(round(ratio * P))))

        try:
            aux = self.problem.parts.aux_values(inst, sol)
        except Exception:
            aux = {}
        times = []  # (start, m, q)
        mk = 0.0
        for m in machines:
            s = info[m][1]
            for q in range(len(s)):
                t = float(aux.get(f"T_{m}_{q}", 0.0))
                times.append((t, m, q))
                j = s[q]
                if j is not None:
                    k = inst.op_index(j, m)
                    if k is not None:
                        mk = max(mk, t + float(inst.proc(j, k)))
        mk = max(mk, max((t for t, _, _ in times), default=0.0), 1.0)

        L = max(1.0, ratio * mk)
        t0 = rng.uniform(0.0, max(0.0, mk - L))
        center = t0 + L / 2.0
        sel = []
        for _ in range(60):
            lo, hi = center - L / 2.0, center + L / 2.0
            sel = [(t, m, q) for (t, m, q) in times if lo - 1e-9 <= t <= hi + 1e-9]
            if len(sel) >= target or L > 2.0 * mk + 2.0:
                break
            L *= 1.25
        if len(sel) < target:
            sel = list(times)
        if len(sel) > target:
            rng.shuffle(sel)
            sel.sort(key=lambda r: abs(r[0] - center))
            sel = sel[:target]

        per_m = {}
        for _, m, q in sel:
            per_m.setdefault(m, set()).add(q)
        free = set()
        for m, qs in per_m.items():
            _free_window(m, info[m], sorted(qs), free)
        free &= set(assign.keys())
        if not free:
            keys = sorted(assign.keys())
            free = {keys[rng.randrange(len(keys))]}
        partial = {v: val for v, val in assign.items() if v not in free}
        return partial, free


def build_component(problem, ratio=0.2):
    return TimeSliceDestruction(problem, ratio=ratio)
