from generated.clsp_setups_cycle.model.parts import canonical

COMPONENT = {
    "name": "same_period_item_pair_toggle",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class SamePeriodItemPairToggle:
    """Movimiento = (t, i, j) con i < j: alterna a la vez los setups (i, t) y (j, t).
    Uno activo y otro no: transfiere la capacidad del período entre ítems.
    Ambos activos: elimina dos setups. Ambos inactivos: abre dos.
    Si solo hay un ítem, el movimiento es (t, 0, 0) y alterna un único setup."""

    def __init__(self, problem):
        self.problem = problem
        self.n = problem.inst.n_items
        self.T = problem.inst.n_periods

    def _all_moves(self, sol):
        out = []
        if self.n < 2:
            for t in range(self.T):
                out.append((t, 0, 0))
            return out
        for t in range(self.T):
            for i in range(self.n):
                for j in range(i + 1, self.n):
                    out.append((t, i, j))
        return out

    def moves(self, sol):
        return iter(self._all_moves(canonical(sol)))

    def sample(self, sol, k, rng):
        allm = self._all_moves(canonical(sol))
        return rng.sample(allm, min(k, len(allm)))

    def apply(self, sol, m):
        t, i, j = m
        s = [list(r) for r in canonical(sol)]
        s[i][t] = not s[i][t]
        if j != i:
            s[j][t] = not s[j][t]
        return canonical(s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem):
    return SamePeriodItemPairToggle(problem)
