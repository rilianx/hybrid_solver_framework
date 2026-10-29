from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "two_opt_intra_and_star",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {
        "star_weight": {"type": "float", "range": [0.0, 1.0]},
    },
}


class TwoOptIntraAndStar:
    """Reconexión de arcos: 
    ("intra", r, i, j): invierte route[i..j] (2-opt clásico dentro de una ruta).
    ("star", a, b, i, j, mode): corta A tras i y B tras j y reconecta:
        mode 0: A[:i]+B[j:] y B[:j]+A[i:]
        mode 1: A[:i]+rev(B[:j]) y rev(A[i:])+B[j:]
    ("noop",) solo si no existe ningún otro movimiento."""

    def __init__(self, problem, star_weight=0.6):
        self.problem = problem
        self.star_weight = float(star_weight)
        self._memo_sol = None
        self._memo_val = None

    def _obj(self, sol):
        if self._memo_sol is not None and self._memo_sol == sol:
            return self._memo_val
        v = self.problem.objective(sol)
        self._memo_sol, self._memo_val = sol, v
        return v

    def _star_ok(self, sol, a, b, i, j, mode):
        la, lb = len(sol[a]), len(sol[b])
        if mode == 0 and ((i == 0 and j == 0) or (i == la and j == lb)):
            return False
        return True

    def _has_real(self, sol):
        return len(sol) >= 2 or any(len(r) >= 2 for r in sol)

    def moves(self, sol):
        nr = len(sol)
        found = False
        for r in range(nr):
            n = len(sol[r])
            for i in range(n - 1):
                for j in range(i + 1, n):
                    found = True
                    yield ("intra", r, i, j)
        for a in range(nr):
            for b in range(a + 1, nr):
                for i in range(len(sol[a]) + 1):
                    for j in range(len(sol[b]) + 1):
                        for mode in (0, 1):
                            if self._star_ok(sol, a, b, i, j, mode):
                                found = True
                                yield ("star", a, b, i, j, mode)
        if not found:
            yield ("noop",)

    def sample(self, sol, k, rng):
        nr = len(sol)
        if not self._has_real(sol):
            return [("noop",)]
        intra_routes = [r for r in range(nr) if len(sol[r]) >= 2]
        out, seen = [], set()
        attempts = 0
        while len(out) < k and attempts < 50 * k + 200:
            attempts += 1
            use_star = nr >= 2 and (not intra_routes or rng.random() < self.star_weight)
            if use_star:
                a, b = sorted(rng.sample(range(nr), 2))
                i = rng.randint(0, len(sol[a]))
                j = rng.randint(0, len(sol[b]))
                mode = rng.randint(0, 1)
                if not self._star_ok(sol, a, b, i, j, mode):
                    continue
                m = ("star", a, b, i, j, mode)
            else:
                r = rng.choice(intra_routes)
                n = len(sol[r])
                i = rng.randint(0, n - 2)
                j = rng.randint(i + 1, n - 1)
                m = ("intra", r, i, j)
            if m in seen:
                continue
            seen.add(m)
            out.append(m)
        if not out:
            for m in self.moves(sol):
                out.append(m)
                break
        return out

    def apply(self, sol, m):
        if m[0] == "noop":
            return canonical(sol)
        routes = [tuple(r) for r in sol]
        if m[0] == "intra":
            _, r, i, j = m
            route = routes[r]
            routes[r] = route[:i] + route[i:j + 1][::-1] + route[j + 1:]
        else:
            _, a, b, i, j, mode = m
            A, B = routes[a], routes[b]
            if mode == 0:
                na = A[:i] + B[j:]
                nb = B[:j] + A[i:]
            else:
                na = A[:i] + B[:j][::-1]
                nb = A[i:][::-1] + B[j:]
            routes[a], routes[b] = na, nb
        return canonical(tuple(routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self._obj(sol)


def build_component(problem, star_weight=0.6):
    return TwoOptIntraAndStar(problem, star_weight=star_weight)
