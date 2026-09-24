COMPONENT = {
    "name": "single_item_two_period_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "radius": {"type": "int", "range": [1, 4]},
    },
}


class SingleItemTwoPeriodSwapNeighborhood:
    """Intercambia un setup de un ítem entre dos períodos cercanos.

    Movimiento: (i, t_out, t_in)
    - apaga sol[i][t_out]
    - enciende sol[i][t_in]
    Es un movimiento de "desplazamiento" local, distinto a fusionar setups.
    """

    def __init__(self, problem, radius=1):
        self.problem = problem
        self.radius = int(radius)

    def moves(self, sol):
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        r = max(1, self.radius)
        for i in range(n_items):
            on = [t for t in range(n_periods) if sol[i][t]]
            off = [t for t in range(n_periods) if not sol[i][t]]
            if not on or not off:
                continue
            for t_out in on:
                lo = max(0, t_out - r)
                hi = min(n_periods - 1, t_out + r)
                for t_in in range(lo, hi + 1):
                    if t_in != t_out and not sol[i][t_in]:
                        yield (i, t_out, t_in)

    def apply(self, sol, m):
        i, t_out, t_in = m
        s = [list(row) for row in sol]
        s[i][t_out] = False
        s[i][t_in] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t_out, t_in = m
        s = [list(row) for row in sol]
        s[i][t_out] = True
        s[i][t_in] = False
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, radius=1):
    return SingleItemTwoPeriodSwapNeighborhood(problem, radius=radius)
