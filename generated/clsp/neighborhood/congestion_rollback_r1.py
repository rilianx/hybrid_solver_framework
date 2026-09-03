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
    """Mueve un setup desde un período congestionado a uno anterior con holgura.
    Movimiento = (i, t, u) con u < t; se apaga (i,t) y se enciende (i,u).
    """

    def __init__(self, problem, slack_margin=5.0):
        self.problem = problem
        self.slack_margin = float(slack_margin)

    def _period_load(self, sol, t):
        inst = self.problem.inst
        prod = sum(inst.demand[i][t] for i in range(inst.n_items) if sol[i][t])
        st = sum(inst.setup_time[i] for i in range(inst.n_items) if sol[i][t])
        return prod + st

    def moves(self, sol):
        inst = self.problem.inst
        loads = [self._period_load(sol, t) for t in range(inst.n_periods)]
        for i in range(inst.n_items):
            for t in range(1, inst.n_periods):
                if not sol[i][t]:
                    continue
                for u in range(t - 1, -1, -1):
                    if sol[i][u]:
                        continue
                    if loads[u] + inst.demand[i][u] + inst.setup_time[i] <= inst.capacity[u] + self.slack_margin:
                        yield (i, t, u)
                        break

    def apply(self, sol, m):
        i, t, u = m
        rows = []
        for ii, row in enumerate(sol):
            if ii != i:
                rows.append(tuple(row))
                continue
            new_row = list(row)
            new_row[t] = False
            new_row[u] = True
            rows.append(tuple(new_row))
        return tuple(rows)

    def undo(self, sol, m):
        i, t, u = m
        rows = []
        for ii, row in enumerate(sol):
            if ii != i:
                rows.append(tuple(row))
                continue
            new_row = list(row)
            new_row[t] = True
            new_row[u] = False
            rows.append(tuple(new_row))
        return tuple(rows)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CongestionRollback(problem, **params)
