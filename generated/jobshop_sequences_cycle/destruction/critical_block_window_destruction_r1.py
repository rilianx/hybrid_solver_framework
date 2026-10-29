from random import Random

from generated.jobshop_sequences_cycle.model.parts import canonical

COMPONENT = {
    "name": "critical_block_window_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "parts.aux_values"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "expand": {"type": "int", "range": [0, 3]},
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


class CriticalBlockWindowDestruction:
    """Libera ventanas (ampliadas) alrededor de los bloques del camino crítico en cada máquina."""

    def __init__(self, problem, ratio=0.2, expand=1):
        self.problem = problem
        self.inst = problem.inst
        self.ratio = ratio
        self.expand = expand

    def _critical_positions(self, sol, info, rng):
        inst = self.inst
        try:
            aux = self.problem.parts.aux_values(inst, sol)
        except Exception:
            return {}
        pos_of = {}
        for m, (_, s) in info.items():
            for q, j in enumerate(s):
                if j is not None:
                    pos_of[(m, j)] = q
        start, fin = {}, {}
        for (m, j), q in pos_of.items():
            k = inst.op_index(j, m)
            st = float(aux.get(f"S_{j}_{k}", 0.0))
            start[(m, j)] = st
            fin[(m, j)] = st + float(inst.proc(j, k))
        if not fin:
            return {}
        mk = max(fin.values())
        ends = [o for o, f in fin.items() if abs(f - mk) < 1e-6]
        cur = ends[rng.randrange(len(ends))]
        crit = {}
        guard = len(fin) + 1
        while cur is not None and guard > 0:
            guard -= 1
            m, j = cur
            crit.setdefault(m, set()).add(pos_of[cur])
            st = start[cur]
            if st <= 1e-6:
                break
            preds = []
            k = inst.op_index(j, m)
            if k > 0:
                pm = inst.machine(j, k - 1)
                if (pm, j) in fin and abs(fin[(pm, j)] - st) < 1e-6:
                    preds.append((pm, j))
            q = pos_of[cur]
            if q > 0:
                pj = info[m][1][q - 1]
                if pj is not None and (m, pj) in fin and abs(fin[(m, pj)] - st) < 1e-6:
                    preds.append((m, pj))
            cur = preds[rng.randrange(len(preds))] if preds else None
        return crit

    def destroy(self, sol, ratio: float, rng: Random):
        sol = canonical(sol)
        if ratio is None:
            ratio = self.ratio
        assign = self.problem.to_assignment(sol)
        info = _structure(assign)
        machines = [m for m in info if len(info[m][0]) > 0]
        P = sum(len(info[m][0]) for m in machines)
        target = min(P, max(2, int(round(ratio * P))))
        freed = {m: set() for m in machines}
        count = 0

        crit = self._critical_positions(sol, info, rng)
        blocks = []
        for m, qs in crit.items():
            qs = sorted(qs)
            b = [qs[0]]
            for q in qs[1:]:
                if q == b[-1] + 1:
                    b.append(q)
                else:
                    blocks.append((m, b))
                    b = [q]
            blocks.append((m, b))
        rng.shuffle(blocks)
        # Prioriza bloques de tamaño >= 2 (los que admiten intercambios útiles).
        blocks.sort(key=lambda mb: 0 if len(mb[1]) >= 2 else 1)
        for m, b in blocks:
            if count >= target:
                break
            n = len(info[m][0])
            lo = max(0, b[0] - rng.randint(0, self.expand))
            hi = min(n - 1, b[-1] + rng.randint(0, self.expand))
            for q in range(lo, hi + 1):
                if q not in freed[m]:
                    freed[m].add(q)
                    count += 1
        guard = 0
        while count < target and machines and guard < 10 * P + 10:
            guard += 1
            m = machines[rng.randrange(len(machines))]
            n = len(info[m][0])
            w = min(n, max(2, target - count))
            lo = rng.randint(0, n - w)
            for q in range(lo, lo + w):
                if q not in freed[m]:
                    freed[m].add(q)
                    count += 1

        free = set()
        for m in machines:
            if freed[m]:
                _free_window(m, info[m], sorted(freed[m]), free)
        free &= set(assign.keys())
        if not free:
            keys = sorted(assign.keys())
            free = {keys[rng.randrange(len(keys))]}
        partial = {v: val for v, val in assign.items() if v not in free}
        return partial, free


def build_component(problem, ratio=0.2, expand=1):
    return CriticalBlockWindowDestruction(problem, ratio=ratio, expand=expand)
