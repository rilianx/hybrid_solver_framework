from generated.clsp_setups_cycle.model.parts import canonical

COMPONENT = {
    "name": "wagner_whitin_row_reopt",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {
        "n_factors": {"type": "int", "range": [1, 5]},
    },
}


class WagnerWhitinRowReopt:
    """Movimiento = (i, k): sustituye la fila de setups del ítem i por la solución
    Wagner-Whitin (con cota de capacidad de un solo ítem) usando holding × factor_k."""

    def __init__(self, problem, n_factors=3):
        self.problem = problem
        inst = problem.inst
        self.n = inst.n_items
        self.T = inst.n_periods
        n_factors = max(1, int(n_factors))
        mid = (n_factors - 1) / 2.0
        self.factors = [2.0 ** (k - mid) for k in range(n_factors)]
        self.rows = {}
        for i in range(self.n):
            for k, f in enumerate(self.factors):
                self.rows[(i, k)] = self._ww_row(inst, i, f)

    def _ww_row(self, inst, i, factor):
        T = self.T
        d = [float(x) for x in inst.demand[i]]
        s = float(inst.setup_cost[i])
        h = float(inst.holding_cost[i]) * factor
        st = float(inst.setup_time[i])
        cap = [float(c) for c in inst.capacity]
        INF = float("inf")
        f = [INF] * (T + 1)
        choice = [None] * (T + 1)
        f[0] = 0.0
        for t in range(1, T + 1):
            for k in range(t):
                if f[k] == INF:
                    continue
                seg = d[k:t]
                tot = sum(seg)
                if tot <= 1e-12:
                    c = f[k]
                    if c < f[t] - 1e-12:
                        f[t] = c
                        choice[t] = (k, False)
                    continue
                if tot > cap[k] - st + 1e-9:
                    continue
                hold = sum(h * (u - k) * d[u] for u in range(k, t))
                c = f[k] + s + hold
                if c < f[t] - 1e-12:
                    f[t] = c
                    choice[t] = (k, True)
        row = [False] * T
        if f[T] == INF:
            return tuple(True for _ in range(T))
        t = T
        while t > 0:
            k, setup = choice[t]
            if setup:
                row[k] = True
            t = k
        return tuple(row)

    def _all_moves(self, sol):
        out = []
        for i in range(self.n):
            seen = set()
            for k in range(len(self.factors)):
                r = self.rows[(i, k)]
                if r != sol[i] and r not in seen:
                    seen.add(r)
                    out.append((i, k))
        if not out:
            out = [(i, k) for i in range(self.n) for k in range(len(self.factors))]
        return out

    def moves(self, sol):
        return iter(self._all_moves(canonical(sol)))

    def sample(self, sol, k, rng):
        allm = self._all_moves(canonical(sol))
        return rng.sample(allm, min(k, len(allm)))

    def apply(self, sol, m):
        i, k = m
        s = [list(r) for r in canonical(sol)]
        s[i] = list(self.rows[(i, k)])
        return canonical(s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, n_factors=3):
    return WagnerWhitinRowReopt(problem, n_factors=n_factors)
