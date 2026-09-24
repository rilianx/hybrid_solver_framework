COMPONENT = {
    "name": "capacity_based_setup_toggle",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "window": {"type": "int", "range": [1, 6]},
        "slack_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class CapacityBasedSetupToggleNeighborhood:
    """Activa o desactiva un setup en períodos que parecen útiles por holgura/carga.

    Movimiento: (i, t, action)
    - action = 0: apagar sol[i][t]
    - action = 1: encender sol[i][t]
    El vecindario prioriza períodos con más holgura de capacidad y cercanía a demanda futura.
    """

    def __init__(self, problem, window=2, slack_bias=0.5):
        self.problem = problem
        self.window = int(window)
        self.slack_bias = float(slack_bias)

    def moves(self, sol):
        inst = self.problem.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        w = max(1, self.window)

        period_slack = []
        for t in range(n_periods):
            used = sum(inst.setup_time[i] for i in range(n_items) if sol[i][t])
            used += sum(inst.demand[i][t] for i in range(n_items) if sol[i][t])
            period_slack.append(inst.capacity[t] - used)

        ranked_periods = sorted(range(n_periods), key=lambda t: (period_slack[t], -t), reverse=True)

        for t in ranked_periods:
            lo = max(0, t - w)
            hi = min(n_periods - 1, t + w)
            for i in range(n_items):
                if sol[i][t]:
                    yield (i, t, 0)
                else:
                    if any(sol[i][tt] for tt in range(lo, hi + 1) if tt != t):
                        yield (i, t, 1)

    def apply(self, sol, m):
        i, t, action = m
        s = [list(row) for row in sol]
        s[i][t] = bool(action)
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t, action = m
        s = [list(row) for row in sol]
        s[i][t] = not bool(action)
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, window=2, slack_bias=0.5):
    return CapacityBasedSetupToggleNeighborhood(problem, window=window, slack_bias=slack_bias)
