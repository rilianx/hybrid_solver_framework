COMPONENT = {
    "name": "intra_route_2opt_reversal",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "problem.parts.canonical"],
    "params": {},
}


class IntraRoute2OptReversalNeighborhood:
    """Invierte un segmento contiguo dentro de una ruta: operador 2-opt intrarruta."""

    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def _routes(self, sol):
        return self.canonical(sol)

    def moves(self, sol):
        routes = self._routes(sol)
        for r_idx, route in enumerate(routes):
            n = len(route)
            if n < 3:
                continue
            for i in range(n - 1):
                for j in range(i + 2, n + 1):
                    yield (r_idx, i, j)

    def apply(self, sol, m):
        r_idx, i, j = m
        routes = [list(route) for route in self._routes(sol)]
        routes[r_idx][i:j] = reversed(routes[r_idx][i:j])
        return self.canonical(tuple(tuple(route) for route in routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)

    def sample(self, sol, k, rng):
        pool = list(self.moves(sol))
        if not pool:
            return []
        if k >= len(pool):
            rng.shuffle(pool)
            return pool
        return rng.sample(pool, k)


def build_component(problem, **params):
    return IntraRoute2OptReversalNeighborhood(problem)
