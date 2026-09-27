COMPONENT = {
    "name": "inter_route_customer_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "problem.parts.canonical"],
    "params": {},
}


class InterRouteCustomerSwapNeighborhood:
    """Intercambia un cliente de una ruta por otro cliente de otra ruta."""

    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def _routes(self, sol):
        return self.canonical(sol)

    def moves(self, sol):
        routes = self._routes(sol)
        nr = len(routes)
        for r1 in range(nr):
            for r2 in range(r1 + 1, nr):
                for i in range(len(routes[r1])):
                    for j in range(len(routes[r2])):
                        yield (r1, i, r2, j)

    def apply(self, sol, m):
        r1, i, r2, j = m
        routes = [list(route) for route in self._routes(sol)]
        routes[r1][i], routes[r2][j] = routes[r2][j], routes[r1][i]
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
    return InterRouteCustomerSwapNeighborhood(problem)
