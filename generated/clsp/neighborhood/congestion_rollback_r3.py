COMPONENT = {
    "name": "congestion_rollback",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "slack_margin": {"type": "float", "range": [0.0, 50.0]},
    },
}

from examples.lotsizing.problem_model import LotSizingModel


class CongestionRollback:
    """Vecindario elemental: flip de un único setup (i, t).

    Mantiene la idea de "rollback" de congestión con movimientos simples de
    un solo bit. Se incluyen tanto activaciones como desactivaciones, siempre
    que la solución resultante sea factible, para evitar vecindarios vacíos.
    """

    def __init__(self, problem, slack_margin=5.0):
        self.problem = problem
        self.slack_margin = float(slack_margin)

    def _flip(self, sol, i, t):
        rows = []
        for ii, row in enumerate(sol):
            if ii != i:
                rows.append(tuple(row))
            else:
                new_row = list(row)
                new_row[t] = not new_row[t]
                rows.append(tuple(new_row))
        return tuple(rows)

    def moves(self, sol):
        inst = self.problem.inst
        for i in range(inst.n_items):
            for t in range(inst.n_periods):
                cand = self._flip(sol, i, t)
                if self.problem.is_feasible(cand):
                    yield (i, t)

    def apply(self, sol, m):
        i, t = m
        return self._flip(sol, i, t)

    def undo(self, sol, m):
        i, t = m
        return self._flip(sol, i, t)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CongestionRollback(problem, **params)
