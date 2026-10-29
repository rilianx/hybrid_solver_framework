from generated.cvrp_tour_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "inter_route_tail_exchange",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective", "ProblemModel.parts"],
    "params": {
        "variants": {"type": "cat", "values": ["tails", "both"]},
    },
}


class InterRouteTailExchange:
    """2-opt* sobre las rutas del Split: corta la ruta a en i y la b en j y recombina.
    flag 0: a[:i]+b[j:], b[:j]+a[i:];  flag 1: a[:i]+rev(b[:j]), rev(a[i:])+b[j:].
    Movimiento = ('x', a, i, b, j, flag); respaldo ('s', p, q) intercambia dos posiciones."""

    def __init__(self, problem, variants="both"):
        self.problem = problem
        self.flags = (0,) if variants == "tails" else (0, 1)

    def _routes(self, sol):
        routes, _ = self.problem.parts._decode(self.problem.inst, canonical(sol))
        return routes

    def _all_moves(self, sol):
        sol = canonical(sol)
        routes = self._routes(sol)
        out = []
        R = len(routes)
        for a in range(R):
            la = len(routes[a])
            for b in range(a + 1, R):
                lb = len(routes[b])
                for i in range(la + 1):
                    for j in range(lb + 1):
                        for f in self.flags:
                            if f == 0 and ((i == 0 and j == 0) or (i == la and j == lb)):
                                continue
                            if f == 1 and ((i == 0 and j == 0) or (i == la and j == lb)):
                                continue
                            out.append(("x", a, i, b, j, f))
        if not out:
            m = len(sol)
            for p in range(m):
                for q in range(p + 1, m):
                    out.append(("s", p, q))
        if not out:
            out.append(("s", 0, 0))
        return out

    def moves(self, sol):
        return iter(self._all_moves(sol))

    def sample(self, sol, k, rng):
        allm = self._all_moves(sol)
        return rng.sample(allm, min(int(k), len(allm)))

    def apply(self, sol, m):
        sol = canonical(sol)
        if m[0] == "s":
            _, p, q = m
            s = list(sol)
            if 0 <= p < len(s) and 0 <= q < len(s):
                s[p], s[q] = s[q], s[p]
            return canonical(s)
        _, a, i, b, j, f = m
        routes = [list(r) for r in self._routes(sol)]
        if not (0 <= a < len(routes) and 0 <= b < len(routes)) or a == b:
            return sol
        ra, rb = routes[a], routes[b]
        if not (0 <= i <= len(ra) and 0 <= j <= len(rb)):
            return sol
        if f == 0:
            na = ra[:i] + rb[j:]
            nb = rb[:j] + ra[i:]
        else:
            na = ra[:i] + rb[:j][::-1]
            nb = ra[i:][::-1] + rb[j:]
        routes[a], routes[b] = na, nb
        tour = [c for r in routes for c in r]
        if len(tour) != len(sol):
            return sol
        return canonical(tour)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, variants="both"):
    return InterRouteTailExchange(problem, variants=variants)
