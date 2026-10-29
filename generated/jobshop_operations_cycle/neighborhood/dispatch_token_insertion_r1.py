COMPONENT = {
    "name": "dispatch_token_insertion",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts"],
    "params": {
        "window": {"type": "int", "range": [1, 512]},
    },
}


class DispatchTokenInsertion:
    """Saca el token en la posición i de la permutación con repetición y lo reinserta en j
    (|i-j| <= window). Cambia a la vez el orden en varias máquinas. Movimiento = (i, j)."""

    def __init__(self, problem, window=512):
        self.problem = problem
        self.parts = problem.parts
        self.window = max(1, int(window))

    def _valid(self, sol, i, j):
        return i != j and sol[i] != sol[j]

    def moves(self, sol):
        sol = tuple(sol)
        L = len(sol)
        out = []
        w = self.window
        for i in range(L):
            lo = max(0, i - w)
            hi = min(L - 1, i + w)
            for j in range(lo, hi + 1):
                if self._valid(sol, i, j):
                    out.append((i, j))
        if not out:
            out = [(0, 0)]
        return out

    def sample(self, sol, k, rng):
        sol = tuple(sol)
        L = len(sol)
        chosen = []
        seen = set()
        if L < 2:
            return [(0, 0)]
        w = self.window
        tries = 0
        limit = 20 * max(1, k) + 50
        while len(chosen) < k and tries < limit:
            tries += 1
            i = rng.randrange(L)
            lo = max(0, i - w)
            hi = min(L - 1, i + w)
            j = rng.randint(lo, hi)
            if not self._valid(sol, i, j) or (i, j) in seen:
                continue
            seen.add((i, j))
            chosen.append((i, j))
        if not chosen:
            allm = list(self.moves(sol))
            rng.shuffle(allm)
            chosen = allm[:max(1, k)]
        return chosen

    def apply(self, sol, m):
        i, j = m
        s = list(sol)
        if 0 <= i < len(s) and 0 <= j < len(s) and i != j:
            x = s.pop(i)
            s.insert(j, x)
        return self.parts.canonical(s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, window=512):
    return DispatchTokenInsertion(problem, window=window)
