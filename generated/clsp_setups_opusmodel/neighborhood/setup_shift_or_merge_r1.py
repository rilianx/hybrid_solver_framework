from generated.clsp_setups_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "setup_shift_or_merge",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "window": {"type": "int", "range": [1, 6]},
    },
}


class SetupShiftOrMerge:
    """Quita el setup (i, t_off) y asegura un setup en (i, t_on), con |t_on - t_off| <= window.
    Si (i, t_on) ya tenía setup, el movimiento fusiona ambos lotes.
    Movimiento = (i, t_off, t_on); -1 indica que esa parte no se aplica (solo como respaldo)."""

    def __init__(self, problem, window=3):
        self.problem = problem
        self.n = problem.inst.n_items
        self.T = problem.inst.n_periods
        self.window = int(window)

    def _list(self, sol):
        plan = canonical(sol)
        out = []
        for i in range(self.n):
            row = plan[i]
            for t in range(self.T):
                if not row[t]:
                    continue
                lo = max(0, t - self.window)
                hi = min(self.T - 1, t + self.window)
                for t2 in range(lo, hi + 1):
                    if t2 != t:
                        out.append((i, t, t2))
        if not out:
            for i in range(self.n):
                for t in range(self.T):
                    if plan[i][t]:
                        out.append((i, t, -1))
                    else:
                        out.append((i, -1, t))
        return out

    def moves(self, sol):
        return iter(self._list(sol))

    def sample(self, sol, k, rng):
        lst = self._list(sol)
        k = max(0, min(int(k), len(lst)))
        return rng.sample(lst, k)

    def apply(self, sol, m):
        i, t_off, t_on = m
        plan = [list(r) for r in canonical(sol)]
        if t_off >= 0:
            plan[i][t_off] = False
        if t_on >= 0:
            plan[i][t_on] = True
        return canonical(plan)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, window=3):
    return SetupShiftOrMerge(problem, window=window)
