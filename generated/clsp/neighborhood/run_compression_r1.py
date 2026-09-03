COMPONENT = {
    "name": "run_compression",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "min_run": {"type": "int", "range": [2, 6]},
    },
}

from examples.lotsizing.problem_model import LotSizingModel


class RunCompression:
    """Comprime una racha consecutiva de setups de un ítem en una sola apertura.
    Movimiento = (i, a, b) con a < b, se mantienen a..a y se apagan a+1..b.
    """

    def __init__(self, problem, min_run=2):
        self.problem = problem
        self.min_run = int(min_run)

    def moves(self, sol):
        inst = self.problem.inst
        L = max(2, self.min_run)
        for i in range(inst.n_items):
            t = 0
            while t < inst.n_periods:
                if not sol[i][t]:
                    t += 1
                    continue
                a = t
                while t + 1 < inst.n_periods and sol[i][t + 1]:
                    t += 1
                b = t
                if b - a + 1 >= L:
                    yield (i, a, b)
                t += 1

    def apply(self, sol, m):
        i, a, b = m
        rows = []
        for ii, row in enumerate(sol):
            if ii != i:
                rows.append(tuple(row))
                continue
            new_row = list(row)
            for t in range(a + 1, b + 1):
                new_row[t] = False
            rows.append(tuple(new_row))
        return tuple(rows)

    def undo(self, sol, m):
        i, a, b = m
        rows = []
        for ii, row in enumerate(sol):
            if ii != i:
                rows.append(tuple(row))
                continue
            new_row = list(row)
            for t in range(a + 1, b + 1):
                new_row[t] = True
            rows.append(tuple(new_row))
        return tuple(rows)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return RunCompression(problem, **params)
