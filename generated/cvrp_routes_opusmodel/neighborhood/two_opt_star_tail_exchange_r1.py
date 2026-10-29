COMPONENT = {
    "name": "two_opt_star_tail_exchange",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective", "ProblemModel.parts"],
    "params": {
        "allow_reverse": {"type": "bool", "values": [True, False]},
    },
}


class TwoOptStarTailExchange:
    """Movimiento = (a, b, i, j, v) con a < b índices de ruta y cortes 0<=i<=|A|, 0<=j<=|B|.

    v=0: A' = A[:i] + B[j:],        B' = B[:j] + A[i:]
    v=1: A' = A[:i] + rev(B[:j]),   B' = rev(A[i:]) + B[j:]
    Los cortes en los extremos permiten fusionar rutas completas (se omiten rutas vacías).
    """

    def __init__(self, problem, allow_reverse=True):
        self.problem = problem
        self.canon = problem.parts.canonical
        self.allow_reverse = bool(allow_reverse)

    def _trivial(self, sol, m):
        a, b, i, j, v = m
        la, lb = len(sol[a]), len(sol[b])
        if v == 0 and ((i == 0 and j == 0) or (i == la and j == lb)):
            return True
        return False

    def _valid(self, sol, m):
        a, b, i, j, v = m
        nR = len(sol)
        if not (0 <= a < b < nR):
            return False
        if not (0 <= i <= len(sol[a]) and 0 <= j <= len(sol[b])):
            return False
        if v not in ((0, 1) if self.allow_reverse else (0,)):
            return False
        return not self._trivial(sol, m)

    def moves(self, sol):
        nR = len(sol)
        vs = (0, 1) if self.allow_reverse else (0,)
        for a in range(nR):
            la = len(sol[a])
            for b in range(a + 1, nR):
                lb = len(sol[b])
                for i in range(la + 1):
                    for j in range(lb + 1):
                        for v in vs:
                            m = (a, b, i, j, v)
                            if self._trivial(sol, m):
                                continue
                            yield m

    def sample(self, sol, k, rng):
        out = []
        seen = set()
        nR = len(sol)
        if nR < 2:
            return out
        vs = (0, 1) if self.allow_reverse else (0,)
        attempts = 0
        while len(out) < k and attempts < 30 * k + 50:
            attempts += 1
            a, b = sorted(rng.sample(range(nR), 2))
            i = rng.randint(0, len(sol[a]))
            j = rng.randint(0, len(sol[b]))
            v = rng.choice(vs)
            m = (a, b, i, j, v)
            if m in seen or not self._valid(sol, m):
                continue
            seen.add(m)
            out.append(m)
        return out

    def apply(self, sol, m):
        a, b, i, j, v = m
        A, B = list(sol[a]), list(sol[b])
        if v == 0:
            na = A[:i] + B[j:]
            nb = B[:j] + A[i:]
        else:
            na = A[:i] + B[:j][::-1]
            nb = A[i:][::-1] + B[j:]
        routes = [list(r) for k2, r in enumerate(sol) if k2 != a and k2 != b]
        routes.append(na)
        routes.append(nb)
        return self.canon(routes)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, allow_reverse=True):
    return TwoOptStarTailExchange(problem, allow_reverse=allow_reverse)
