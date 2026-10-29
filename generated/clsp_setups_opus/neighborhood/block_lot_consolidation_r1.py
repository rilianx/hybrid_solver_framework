from generated.clsp_setups_cycle.model.parts import canonical

COMPONENT = {
    "name": "block_lot_consolidation",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {
        "max_len": {"type": "int", "range": [1, 6]},
    },
}


class BlockLotConsolidation:
    """Movimiento = (i, a, b): setup de i en a, sin setups de i en a+1..b (fusiona lotes).
    Si a == b, alterna el setup (i, a) (solo se usa con un único período)."""

    def __init__(self, problem, max_len=3):
        self.problem = problem
        self.n = problem.inst.n_items
        self.T = problem.inst.n_periods
        self.max_len = max(1, int(max_len))

    def _changes(self, row, a, b):
        if a == b:
            return True
        if not row[a]:
            return True
        return any(row[u] for u in range(a + 1, b + 1))

    def _all_moves(self, sol):
        out = []
        if self.T < 2:
            for i in range(self.n):
                out.append((i, 0, 0))
            return out
        for i in range(self.n):
            row = sol[i]
            for a in range(self.T):
                for b in range(a + 1, min(self.T - 1, a + self.max_len) + 1):
                    if self._changes(row, a, b):
                        out.append((i, a, b))
        if not out:
            for i in range(self.n):
                for t in range(self.T):
                    out.append((i, t, t))
        return out

    def moves(self, sol):
        sol = canonical(sol)
        return iter(self._all_moves(sol))

    def sample(self, sol, k, rng):
        allm = self._all_moves(canonical(sol))
        k = min(k, len(allm))
        return rng.sample(allm, k)

    def apply(self, sol, m):
        i, a, b = m
        s = [list(r) for r in canonical(sol)]
        if a == b:
            s[i][a] = not s[i][a]
        else:
            s[i][a] = True
            for u in range(a + 1, b + 1):
                s[i][u] = False
        return canonical(s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_len=3):
    return BlockLotConsolidation(problem, max_len=max_len)
