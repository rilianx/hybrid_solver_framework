from generated.cvrp_tour_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "decoded_route_two_opt",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective", "ProblemModel.parts"],
    "params": {
        "max_span": {"type": "int", "range": [2, 200]},
    },
}


class DecodedRouteTwoOpt:
    """Decodifica el gran tour con Split, invierte un tramo [i..j] dentro de una ruta y
    re-concatena las rutas. Movimiento = ('r', ruta, i, j); respaldo ('g', i, j) sobre el tour."""

    def __init__(self, problem, max_span=50):
        self.problem = problem
        self.max_span = max(2, int(max_span))

    def _routes(self, sol):
        routes, _ = self.problem.parts._decode(self.problem.inst, canonical(sol))
        return routes

    def _all_moves(self, sol):
        sol = canonical(sol)
        out = []
        for ri, r in enumerate(self._routes(sol)):
            L = len(r)
            for i in range(L - 1):
                for j in range(i + 1, min(L, i + self.max_span)):
                    out.append(("r", ri, i, j))
        if not out:
            m = len(sol)
            for i in range(m - 1):
                for j in range(i + 1, min(m, i + self.max_span)):
                    out.append(("g", i, j))
        if not out:
            out.append(("g", 0, 0))
        return out

    def moves(self, sol):
        return iter(self._all_moves(sol))

    def sample(self, sol, k, rng):
        allm = self._all_moves(sol)
        return rng.sample(allm, min(int(k), len(allm)))

    def apply(self, sol, m):
        sol = canonical(sol)
        kind = m[0]
        if kind == "g":
            _, i, j = m
            s = list(sol)
            if 0 <= i < j < len(s):
                s[i:j + 1] = s[i:j + 1][::-1]
            return canonical(s)
        _, ri, i, j = m
        routes = [list(r) for r in self._routes(sol)]
        if not (0 <= ri < len(routes)) or not (0 <= i < j < len(routes[ri])):
            return sol
        r = routes[ri]
        routes[ri] = r[:i] + r[i:j + 1][::-1] + r[j + 1:]
        tour = [c for r in routes for c in r]
        if len(tour) != len(sol):
            return sol
        return canonical(tour)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_span=50):
    return DecodedRouteTwoOpt(problem, max_span=max_span)
