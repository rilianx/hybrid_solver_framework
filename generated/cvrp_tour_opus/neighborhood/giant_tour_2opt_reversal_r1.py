from generated.cvrp_tour_cycle.model.parts import canonical

COMPONENT = {
    "name": "giant_tour_2opt_reversal",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {
        "max_span": {"type": "int", "range": [2, 200]},
    },
}


class GiantTour2OptReversal:
    """Movimiento = (i, j) con i < j: invierte tour[i:j+1]. Split redecodifica después."""

    def __init__(self, problem, max_span=50):
        self.problem = problem
        self.max_span = max(1, int(max_span))
        self._c_sol = None
        self._c_obj = None

    def _obj(self, sol):
        if self._c_sol is not None and self._c_sol == sol:
            return self._c_obj
        v = self.problem.objective(sol)
        self._c_sol = sol
        self._c_obj = v
        return v

    def moves(self, sol):
        t = canonical(sol)
        n = len(t)
        out = []
        for i in range(n - 1):
            for j in range(i + 1, min(n, i + self.max_span + 1)):
                out.append((i, j))
        return out

    def sample(self, sol, k, rng):
        t = canonical(sol)
        n = len(t)
        if n < 2:
            return []
        res = []
        seen = set()
        attempts = 0
        while len(res) < k and attempts < 30 * max(1, k):
            attempts += 1
            i = rng.randint(0, n - 2)
            j = rng.randint(i + 1, min(n - 1, i + self.max_span))
            m = (i, j)
            if m in seen:
                continue
            seen.add(m)
            res.append(m)
        return res

    def apply(self, sol, m):
        t = canonical(sol)
        i, j = m
        return canonical(t[:i] + tuple(reversed(t[i:j + 1])) + t[j + 1:])

    def delta(self, sol, m):
        sol = canonical(sol)
        return self.problem.objective(self.apply(sol, m)) - self._obj(sol)


def build_component(problem, max_span=50):
    return GiantTour2OptReversal(problem, max_span=max_span)
