COMPONENT = {
    "name": "customer_relocation",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "problem.parts.canonical"],
    "params": {},
}


class CustomerRelocationNeighborhood:
    """Mueve un cliente de su posición actual a otra posición/ruta (inserción)."""

    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def _routes(self, sol):
        return self.canonical(sol)

    def moves(self, sol):
        routes = self._routes(sol)
        for r_idx, route in enumerate(routes):
            for i, c in enumerate(route):
                for rr_idx in range(len(routes)):
                    for j in range(len(routes[rr_idx]) + 1):
                        if rr_idx == r_idx and (j == i or j == i + 1):
                            continue
                        yield (r_idx, i, rr_idx, j)

    def apply(self, sol, m):
        r1, i, r2, j = m
        routes = [list(route) for route in self._routes(sol)]
        c = routes[r1].pop(i)
        if r1 == r2 and j > i:
            j -= 1
        routes[r2].insert(j, c)
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
    return CustomerRelocationNeighborhood(problem)
