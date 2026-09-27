COMPONENT = {
    "name": "customer_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {
        "max_moves": {"type": "int", "range": [10, 500]},
    },
}


class CustomerSwapNeighborhood:
    """Intercambia dos clientes entre rutas o dentro de una misma ruta. Movimiento = (ri, pi, rj, qj)."""

    def __init__(self, problem, max_moves: int = 200):
        self.problem = problem
        self.parts = problem.parts
        self.max_moves = int(max_moves)

    def _routes(self, sol):
        return self.parts.canonical(sol)

    def moves(self, sol):
        routes = self._routes(sol)
        n_routes = len(routes)
        seen = 0

        for i in range(n_routes):
            for p in range(len(routes[i])):
                for j in range(i, n_routes):
                    q0 = p + 1 if j == i else 0
                    for q in range(q0, len(routes[j])):
                        mv = (i, p, j, q)
                        yield mv
                        seen += 1
                        if seen >= self.max_moves:
                            return

    def apply(self, sol, m):
        i, p, j, q = m
        routes = [list(r) for r in self._routes(sol)]
        routes[i][p], routes[j][q] = routes[j][q], routes[i][p]
        return self.parts.canonical(tuple(tuple(r) for r in routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    max_moves = params.get("max_moves", 200)
    return CustomerSwapNeighborhood(problem, max_moves=max_moves)
