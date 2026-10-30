COMPONENT = {
    "name": "earliest_completion_idle_penalty",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "idle_weight": {"type": "float", "range": [0.0, 3.0]},
        "mk_weight": {"type": "float", "range": [0.0, 3.0]},
    },
}


class EarliestCompletionIdlePenalty:
    """Job shop: elige la operación que termina antes (ECT), penalizando el hueco ocioso
    que deja en su máquina (action.idle) y cuánto alarga el makespan parcial.
    Desempate determinista por índice de trabajo. Menor = mejor."""

    def __init__(self, problem, idle_weight=0.5, mk_weight=1.0):
        self.inst = problem.inst
        self.idle_weight = float(idle_weight)
        self.mk_weight = float(mk_weight)
        self.eps = 1e-6 / max(1, self.inst.n_jobs)

    def score(self, partial, action):
        return float(
            action.end
            + self.idle_weight * action.idle
            + self.mk_weight * action.makespan_increase
            + self.eps * action.job
        )


def build_component(problem, idle_weight=0.5, mk_weight=1.0):
    return EarliestCompletionIdlePenalty(problem, idle_weight, mk_weight)
