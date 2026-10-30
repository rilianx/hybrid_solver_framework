COMPONENT = {
    "name": "most_work_remaining_tail_bound",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "start_weight": {"type": "float", "range": [0.5, 4.0]},
        "tail_weight": {"type": "float", "range": [0.0, 2.0]},
    },
}


class MostWorkRemainingTailBound:
    """Job shop: estima la cota inferior del trabajo si se programa ahora
    (end + suma de procesos restantes de su ruta) y prefiere el trabajo más crítico
    (cota mayor), pero penaliza empezar tarde para mantener el plan compacto.
    score = start_weight*start - tail_weight*(proc + cola). Menor = mejor."""

    def __init__(self, problem, start_weight=1.5, tail_weight=1.0):
        inst = problem.inst
        self.inst = inst
        self.start_weight = float(start_weight)
        self.tail_weight = float(tail_weight)
        tails = []
        for j in inst.jobs:
            r = inst.routes[j]
            t = [0] * (len(r) + 1)
            for k in range(len(r) - 1, -1, -1):
                t[k] = t[k + 1] + r[k][1]
            tails.append(tuple(t))
        self.tails = tuple(tails)
        self.eps = 1e-6 / max(1, inst.n_jobs)

    def score(self, partial, action):
        rem = self.tails[action.job][action.op]  # incluye la operación actual
        return float(
            self.start_weight * action.start
            - self.tail_weight * rem
            + self.eps * action.job
        )


def build_component(problem, start_weight=1.5, tail_weight=1.0):
    return MostWorkRemainingTailBound(problem, start_weight, tail_weight)
