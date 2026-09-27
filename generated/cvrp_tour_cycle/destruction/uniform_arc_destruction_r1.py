from random import Random

COMPONENT = {
    "name": "uniform_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class UniformArcDestruction:
    """Libera arcos estructurales al azar, preservando el resto de la asignación."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        vars_ = list(assignment.keys())
        n = len(vars_)
        k = max(1, min(n, int(round(ratio * n))))

        chosen = set(rng.sample(vars_, k))
        partial = {v: val for v, val in assignment.items() if v not in chosen}
        return partial, chosen


def build_component(problem, ratio: float = 0.2):
    return UniformArcDestruction(problem, problem.inst)
