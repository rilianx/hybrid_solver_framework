COMPONENT = {
    "name": "merge_adjacent_setups",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "max_shift": {"type": "int", "range": [1, 6]},
        "prefer_left": {"type": "bool", "range": [0, 1]},
    },
}


class MergeAdjacentSetupsNeighborhood:
    """Fusiona un setup con el setup anterior del mismo ítem, adelantando producción y eliminando setups redundantes.

    Movimiento: (i, t_from, t_to)
    - apaga sol[i][t_from]
    - enciende sol[i][t_to]
    con t_to < t_from y ambos períodos dentro de una ventana limitada por max_shift.
    """

    def __init__(self, problem, max_shift=2, prefer_left=True):
        self.problem = problem
        self.max_shift = int(max_shift)
        self.prefer_left = bool(prefer_left)

    def moves(self, sol):
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        limit = max(1, self.max_shift)
        for i in range(n_items):
            periods = [t for t in range(n_periods) if sol[i][t]]
            if not periods:
                continue
            for t_from in periods:
                candidates = range(max(0, t_from - limit), t_from)
                if self.prefer_left:
                    candidates = list(candidates)
                for t_to in candidates:
                    if not sol[i][t_to]:
                        yield (i, t_from, t_to)

    def apply(self, sol, m):
        i, t_from, t_to = m
        s = [list(row) for row in sol]
        s[i][t_from] = False
        s[i][t_to] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t_from, t_to = m
        s = [list(row) for row in sol]
        s[i][t_from] = True
        s[i][t_to] = False
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_shift=2, prefer_left=True):
    return MergeAdjacentSetupsNeighborhood(problem, max_shift=max_shift, prefer_left=prefer_left)
