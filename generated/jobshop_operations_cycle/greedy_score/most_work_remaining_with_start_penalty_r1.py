COMPONENT = {
    "name": "most_work_remaining_with_start_penalty",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "start_weight": {"type": "float", "range": [0.0, 2.0]},
        "idle_weight": {"type": "float", "range": [0.0, 2.0]},
    },
}


class MostWorkRemainingWithStartPenalty:
    """Regla MWKR: despacha antes el trabajo al que le queda más trabajo
    (incluida la operación candidata). Penaliza empezar tarde y dejar huecos en la máquina."""

    def __init__(self, problem, start_weight: float = 1.0, idle_weight: float = 0.5):
        inst = problem.inst
        self.start_weight = float(start_weight)
        self.idle_weight = float(idle_weight)
        self.suffix = []
        for j in range(inst.n_jobs):
            r = inst.routes[j]
            suf = [0] * (len(r) + 1)
            for k in range(len(r) - 1, -1, -1):
                suf[k] = suf[k + 1] + int(r[k][1])
            self.suffix.append(tuple(suf))

    def score(self, partial, action):
        j = int(action.job)
        k = int(action.op)
        suf = self.suffix[j]
        work_left = suf[k] if 0 <= k < len(suf) else 0
        return float(-work_left
                     + self.start_weight * float(action.start)
                     + self.idle_weight * float(action.idle))


def build_component(problem, start_weight: float = 1.0, idle_weight: float = 0.5):
    return MostWorkRemainingWithStartPenalty(problem, start_weight, idle_weight)
