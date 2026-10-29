COMPONENT = {
    "name": "earliest_completion_compact",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "idle_weight": {"type": "float", "range": [0.0, 3.0]},
        "growth_weight": {"type": "float", "range": [0.0, 3.0]},
    },
}


class EarliestCompletionCompact:
    """Prioriza la operación que termina antes (ECT), favoreciendo planes compactos:
    penaliza el hueco ocioso que deja en su máquina y cuánto hace crecer el makespan parcial."""

    def __init__(self, problem, idle_weight: float = 1.0, growth_weight: float = 0.5):
        self.idle_weight = float(idle_weight)
        self.growth_weight = float(growth_weight)

    def score(self, partial, action):
        return float(float(action.end)
                     + self.idle_weight * float(action.idle)
                     + self.growth_weight * float(action.delta_makespan))


def build_component(problem, idle_weight: float = 1.0, growth_weight: float = 0.5):
    return EarliestCompletionCompact(problem, idle_weight, growth_weight)
