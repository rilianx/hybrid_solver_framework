COMPONENT = {
    "name": "bottleneck_machine_load_priority",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "load_weight": {"type": "float", "range": [0.0, 2.0]},
        "succ_weight": {"type": "float", "range": [0.0, 1.0]},
    },
}


class BottleneckMachineLoadPriority:
    """Job shop: la urgencia viene de la máquina. Cota de la máquina m:
    mready[m] + carga aún no programada en m. Se prefieren operaciones que terminan
    pronto y alimentan máquinas cuello de botella; además se premia que la siguiente
    operación del trabajo vaya a una máquina cargada (pasar trabajo al cuello).
    Menor = mejor."""

    def __init__(self, problem, load_weight=0.7, succ_weight=0.3):
        inst = problem.inst
        self.inst = inst
        self.load_weight = float(load_weight)
        self.succ_weight = float(succ_weight)
        M = inst.n_machines
        proc_on = [dict() for _ in range(M)]
        total = [0] * M
        for j in inst.jobs:
            for (m, p) in inst.routes[j]:
                proc_on[m][j] = p
                total[m] += p
        self.proc_on = tuple(proc_on)
        self.total = tuple(total)
        self.eps = 1e-6 / max(1, inst.n_jobs)

    def _remaining(self, partial, m):
        done = 0
        pm = self.proc_on[m]
        for j in partial.seqs[m]:
            done += pm.get(j, 0)
        return self.total[m] - done

    def score(self, partial, action):
        m = action.machine
        bound_m = partial.mready[m] + self._remaining(partial, m)
        s = action.end - self.load_weight * bound_m
        if self.succ_weight > 0.0:
            route = self.inst.routes[action.job]
            k2 = action.op + 1
            if k2 < len(route):
                m2 = route[k2][0]
                bound_2 = partial.mready[m2] + self._remaining(partial, m2)
                s -= self.succ_weight * bound_2
        return float(s + self.eps * action.job)


def build_component(problem, load_weight=0.7, succ_weight=0.3):
    return BottleneckMachineLoadPriority(problem, load_weight, succ_weight)
