from generated.cvrp_tour_cycle.model.parts import canonical

COMPONENT = {
    "name": "giant_tour_or_opt_segment_shift",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {
        "max_seg_len": {"type": "int", "range": [1, 5]},
        "allow_reverse": {"type": "bool"},
    },
}


class GiantTourOrOptSegmentShift:
    """Movimiento = (i, L, j, rev): extrae tour[i:i+L] y lo reinserta en la posición j
    del tour restante (invertido si rev == 1)."""

    def __init__(self, problem, max_seg_len=3, allow_reverse=True):
        self.problem = problem
        self.max_seg_len = max(1, int(max_seg_len))
        self.allow_reverse = bool(allow_reverse)
        self._c_sol = None
        self._c_obj = None

    def _obj(self, sol):
        if self._c_sol is not None and self._c_sol == sol:
            return self._c_obj
        v = self.problem.objective(sol)
        self._c_sol = sol
        self._c_obj = v
        return v

    def _valid(self, n, m):
        i, L, j, rev = m
        if L < 1 or i < 0 or i + L > n:
            return False
        if j < 0 or j > n - L:
            return False
        if rev not in (0, 1):
            return False
        if j == i and rev == 0:
            return False
        if rev == 1 and L == 1:
            return False
        return True

    def moves(self, sol):
        t = canonical(sol)
        n = len(t)
        revs = (0, 1) if self.allow_reverse else (0,)
        out = []
        for L in range(1, min(self.max_seg_len, n) + 1):
            for i in range(0, n - L + 1):
                for j in range(0, n - L + 1):
                    for rev in revs:
                        m = (i, L, j, rev)
                        if self._valid(n, m):
                            out.append(m)
        if not out and n >= 2:
            out.append((0, 1, 1, 0))
        return out

    def sample(self, sol, k, rng):
        t = canonical(sol)
        n = len(t)
        res = []
        seen = set()
        if n < 2:
            return res
        maxL = min(self.max_seg_len, n - 1) if n > 1 else 1
        maxL = max(1, maxL)
        attempts = 0
        while len(res) < k and attempts < 30 * max(1, k):
            attempts += 1
            L = rng.randint(1, maxL)
            i = rng.randint(0, n - L)
            j = rng.randint(0, n - L)
            rev = rng.randint(0, 1) if (self.allow_reverse and L > 1) else 0
            m = (i, L, j, rev)
            if m in seen or not self._valid(n, m):
                continue
            seen.add(m)
            res.append(m)
        if not res:
            full = self.moves(sol)
            res = rng.sample(full, min(k, len(full)))
        return res

    def apply(self, sol, m):
        t = canonical(sol)
        i, L, j, rev = m
        seg = t[i:i + L]
        if rev:
            seg = tuple(reversed(seg))
        rest = t[:i] + t[i + L:]
        return canonical(tuple(rest[:j]) + tuple(seg) + tuple(rest[j:]))

    def delta(self, sol, m):
        sol = canonical(sol)
        return self.problem.objective(self.apply(sol, m)) - self._obj(sol)


def build_component(problem, max_seg_len=3, allow_reverse=True):
    return GiantTourOrOptSegmentShift(problem, max_seg_len=max_seg_len, allow_reverse=allow_reverse)
