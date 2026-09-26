COMPONENT = {
    "name": "two_opt_segment_reversal_fast",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class TwoOptSegmentReversal:
    """Revierte un segmento contiguo de la gran tour. Movimiento = (i, j) con i < j."""

    __slots__ = ("problem", "_obj_cache", "_delta_cache")

    def __init__(self, problem):
        self.problem = problem
        self._obj_cache = {}
        self._delta_cache = {}

    def moves(self, sol):
        n = len(sol)
        for i in range(n - 1):
            for j in range(i + 1, n):
                yield (i, j)

    def apply(self, sol, m):
        i, j = m
        return sol[:i] + sol[i : j + 1][::-1] + sol[j + 1 :]

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        key = (sol, m)
        cached = self._delta_cache.get(key)
        if cached is not None:
            return cached

        old = self._obj_cache.get(sol)
        if old is None:
            old = self.problem.objective(sol)
            self._obj_cache[sol] = old

        new_sol = self.apply(sol, m)
        new = self._obj_cache.get(new_sol)
        if new is None:
            new = self.problem.objective(new_sol)
            self._obj_cache[new_sol] = new

        d = new - old
        self._delta_cache[key] = d
        return d


def build_component(problem, **params):
    return TwoOptSegmentReversal(problem)
