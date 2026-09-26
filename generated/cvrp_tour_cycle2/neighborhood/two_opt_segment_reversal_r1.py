COMPONENT = {
    "name": "two_opt_segment_reversal",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class TwoOptSegmentReversal:
    """Revierte un segmento contiguo de la gran tour. Movimiento = (i, j) con i < j."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol):
        n = len(sol)
        for i in range(n - 1):
            for j in range(i + 1, n):
                yield (i, j)

    def apply(self, sol, m):
        i, j = m
        s = list(sol)
        s[i : j + 1] = reversed(s[i : j + 1])
        return tuple(s)

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return TwoOptSegmentReversal(problem)
