COMPONENT = {
    "name": "customer_relocate",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {
        "max_moves": {"type": "int", "range": [10, 500]},
    },
}


class CustomerRelocateNeighborhood:
    """Mueve un cliente a otra posición o a otra ruta. Movimiento = (ri, pi, rj, pj)."""

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

        for i, route in enumerate(routes):
            for p, _c in enumerate(route):
                for j in range(n_routes + 1):
                    if j == i:
                        for q in range(len(route)):
                            if q != p:
                                mv = (i, p, j, q)
                                yield mv
                                seen += 1
                                if seen >= self.max_moves:
                                    return
                    else:
                        target_len = len(routes[j]) if j < n_routes else 0
                        for q in range(target_len + 1):
                            mv = (i, p, j, q)
                            yield mv
                            seen += 1
                            if seen >= self.max_moves:
                                return

    def apply(self, sol, m):
        i, p, j, q = m
        routes = [list(r) for r in self._routes(sol)]
        c = routes[i].pop(p)
        if not routes[i]:
            del routes[i]
            if j > i:
                j -= 1

        if j == len(routes):
            routes.append([c])
        else:
            if j == i and q > p:
                q -= 1
            routes[j].insert(q, c)

        return self.parts.canonical(tuple(tuple(r) for r in routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    max_moves = params.get("max_moves", 200)
    return CustomerRelocateNeighborhood(problem, max_moves=max_moves)
