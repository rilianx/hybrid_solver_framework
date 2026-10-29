COMPONENT = {
    "name": "makespan_lower_bound_lookahead",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "job_weight": {"type": "float", "range": [0.5, 1.5]},
        "machine_weight": {"type": "float", "range": [0.5, 1.5]},
        "start_tiebreak": {"type": "float", "range": [0.0, 0.5]},
    },
}


class MakespanLowerBoundLookahead:
    """Puntúa cada acción con una cota inferior del makespan final si se toma:
    max(makespan parcial, fin + cola del trabajo, fin + carga pendiente de la máquina).
    Desempata por el inicio más temprano."""

    def __init__(self, problem, job_weight: float = 1.0, machine_weight: float = 1.0,
                 start_tiebreak: float = 0.1):
        inst = problem.inst
        self.jw = float(job_weight)
        self.mw = float(machine_weight)
        self.tb = float(start_tiebreak)
        self.suffix = []
        mach_ops = [[] for _ in range(inst.n_machines)]
        for j in range(inst.n_jobs):
            r = inst.routes[j]
            suf = [0] * (len(r) + 1)
            for k in range(len(r) - 1, -1, -1):
                suf[k] = suf[k + 1] + int(r[k][1])
            self.suffix.append(tuple(suf))
            for k, (m, p) in enumerate(r):
                if 0 <= m < inst.n_machines:
                    mach_ops[m].append((j, k, int(p)))
        self.mach_ops = tuple(tuple(x) for x in mach_ops)

    def score(self, partial, action):
        j = int(action.job)
        k = int(action.op)
        m = int(action.machine)
        end = float(action.end)
        suf = self.suffix[j]
        tail_job = suf[k + 1] if 0 <= k + 1 < len(suf) else 0
        rem_m = 0
        if 0 <= m < len(self.mach_ops):
            ptr = partial.job_ptr
            for (jj, kk, p) in self.mach_ops[m]:
                if jj == j and kk == k:
                    continue
                if kk >= ptr[jj]:
                    rem_m += p
        lb = max(float(partial.makespan),
                 self.jw * (end + tail_job),
                 self.mw * (end + rem_m))
        return float(lb + self.tb * float(action.start))


def build_component(problem, job_weight: float = 1.0, machine_weight: float = 1.0,
                    start_tiebreak: float = 0.1):
    return MakespanLowerBoundLookahead(problem, job_weight, machine_weight, start_tiebreak)
