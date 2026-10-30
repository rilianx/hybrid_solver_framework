from random import Random

from generated.jobshop_sequences_cycle.model.parts import canonical

COMPONENT = {
    "name": "related_jobs_slot_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "relatedness": {"type": "float", "range": [0.0, 1.0]},
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


class RelatedJobsSlotDestruction:
    """Elige un grupo de trabajos relacionados (vecinos en las secuencias) y los libera:
    en cada máquina pueden permutarse entre sí dentro de las posiciones que ocupan."""

    def __init__(self, problem, ratio=0.2, relatedness=0.7):
        self.problem = problem
        self.ratio = ratio
        self.relatedness = relatedness

    def destroy(self, sol, ratio: float, rng: Random):
        sol = canonical(sol)
        if ratio is None:
            ratio = self.ratio
        assign = self.problem.to_assignment(sol)
        info = _structure(assign)
        machines = [m for m in info if len(info[m][0]) > 0]
        P = sum(len(info[m][0]) for m in machines)
        target = min(P, max(2, int(round(ratio * P))))

        load = {}
        neigh = {}
        for m in machines:
            jobs, s = info[m]
            for j in jobs:
                load[j] = load.get(j, 0) + 1
                neigh.setdefault(j, set())
            for q in range(len(s) - 1):
                a, b = s[q], s[q + 1]
                if a is not None and b is not None:
                    neigh[a].add(b)
                    neigh[b].add(a)
        all_jobs = sorted(load.keys())
        chosen = set()
        count = 0
        if all_jobs:
            seed = all_jobs[rng.randrange(len(all_jobs))]
            chosen.add(seed)
            count += load[seed]
        while count < target and len(chosen) < len(all_jobs):
            frontier = sorted({k for j in chosen for k in neigh.get(j, ()) if k not in chosen})
            if frontier and rng.random() < self.relatedness:
                j = frontier[rng.randrange(len(frontier))]
            else:
                rest = [k for k in all_jobs if k not in chosen]
                j = rest[rng.randrange(len(rest))]
            chosen.add(j)
            count += load[j]

        free = set()
        for m in machines:
            jobs, s = info[m]
            placed = {x for x in s if x is not None}
            missing_chosen = any(j in chosen and j not in placed for j in jobs)
            qs = [q for q in range(len(s))
                  if s[q] in chosen or (s[q] is None and missing_chosen)]
            if qs:
                _free_window(m, info[m], qs, free)
        free &= set(assign.keys())
        if not free:
            keys = sorted(assign.keys())
            free = {keys[rng.randrange(len(keys))]}
        partial = {v: val for v, val in assign.items() if v not in free}
        return partial, free


def build_component(problem, ratio=0.2, relatedness=0.7):
    return RelatedJobsSlotDestruction(problem, ratio=ratio, relatedness=relatedness)
