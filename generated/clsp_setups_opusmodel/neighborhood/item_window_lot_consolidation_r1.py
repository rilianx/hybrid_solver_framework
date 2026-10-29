from generated.clsp_setups_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "item_window_lot_consolidation",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "max_len": {"type": "int", "range": [2, 8]},
    },
}


class ItemWindowLotConsolidation:
    """Para el ítem i y la ventana [a, b], deja un único setup en a y cierra los de a+1..b:
    un solo lote cubre la demanda de varios períodos (estilo Wagner-Whitin).
    Movimiento = (i, a, b) con a < b; (i, a, a) invierte (i, a) y solo se usa como respaldo."""

    def __init__(self, problem, max_len=4):
        self.problem = problem
        self.n = problem.inst.n_items
        self.T = problem.inst.n_periods
        self.max_len = int(max_len)

    def _list(self, sol):
        plan = canonical(sol)
        out = []
        for i in range(self.n):
            row = plan[i]
            for a in range(self.T):
                for b in range(a + 1, min(self.T, a + self.max_len)):
                    if (not row[a]) or any(row[a + 1:b + 1]):
                        out.append((i, a, b))
        if not out:
            out = [(i, a, a) for i in range(self.n) for a in range(self.T)]
        return out

    def moves(self, sol):
        return iter(self._list(sol))

    def sample(self, sol, k, rng):
        lst = self._list(sol)
        k = max(0, min(int(k), len(lst)))
        return rng.sample(lst, k)

    def apply(self, sol, m):
        i, a, b = m
        plan = [list(r) for r in canonical(sol)]
        if a == b:
            plan[i][a] = not plan[i][a]
        else:
            plan[i][a] = True
            for t in range(a + 1, b + 1):
                plan[i][t] = False
        return canonical(plan)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_len=4):
    return ItemWindowLotConsolidation(problem, max_len=max_len)
