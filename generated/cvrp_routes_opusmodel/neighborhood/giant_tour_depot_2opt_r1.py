COMPONENT = {
    "name": "giant_tour_depot_2opt",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective", "ProblemModel.parts"],
    "params": {
        "max_span": {"type": "int", "range": [2, 200]},
    },
}


class GiantTourDepot2Opt:
    """Representa la solución como tour gigante G = [0] + r1 + [0] + r2 + ... + [0].

    Movimiento = (i, j), 1 <= i < j <= len(G)-2, j-i+1 <= max_span: invierte G[i..j] y vuelve a
    cortar por los ceros. Invertir dentro de una ruta es 2-opt clásico; invertir a través de un
    depósito mueve el corte de ruta (fusiona, divide o reasigna clientes entre rutas contiguas).
    """

    def __init__(self, problem, max_span=50):
        self.problem = problem
        self.canon = problem.parts.canonical
        self.max_span = max(2, int(max_span))

    @staticmethod
    def _giant(sol):
        g = [0]
        for r in sol:
            g.extend(int(c) for c in r)
            g.append(0)
        return g

    def moves(self, sol):
        g = self._giant(sol)
        L = len(g)
        for i in range(1, L - 2):
            for j in range(i + 1, min(L - 2, i + self.max_span - 1) + 1):
                if g[i] == 0 and g[j] == 0 and j - i == 1:
                    continue
                yield (i, j)

    def sample(self, sol, k, rng):
        g = self._giant(sol)
        L = len(g)
        out = []
        seen = set()
        if L < 4:
            return out
        attempts = 0
        while len(out) < k and attempts < 30 * k + 50:
            attempts += 1
            i = rng.randint(1, L - 3)
            hi = min(L - 2, i + self.max_span - 1)
            if hi <= i:
                continue
            j = rng.randint(i + 1, hi)
            if g[i] == 0 and g[j] == 0 and j - i == 1:
                continue
            m = (i, j)
            if m in seen:
                continue
            seen.add(m)
            out.append(m)
        return out

    def apply(self, sol, m):
        i, j = m
        g = self._giant(sol)
        g2 = g[:i] + g[i:j + 1][::-1] + g[j + 1:]
        routes = []
        cur = []
        for x in g2:
            if x == 0:
                if cur:
                    routes.append(cur)
                cur = []
            else:
                cur.append(x)
        if cur:
            routes.append(cur)
        return self.canon(routes)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_span=50):
    return GiantTourDepot2Opt(problem, max_span=max_span)
