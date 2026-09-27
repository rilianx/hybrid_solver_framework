COMPONENT = {
    "name": "route_segment_reinsertion",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {
        "max_moves": {"type": "int", "range": [10, 500]},
        "max_segment_len": {"type": "int", "range": [1, 10]},
    },
}


class RouteSegmentReinsertionNeighborhood:
    """Extrae un segmento contiguo de una ruta y lo inserta en otra posición/ruta. Movimiento = (ri, a, b, rj, q)."""

    def __init__(self, problem, max_moves: int = 200, max_segment_len: int = 4):
        self.problem = problem
        self.parts = problem.parts
        self.max_moves = int(max_moves)
        self.max_segment_len = int(max_segment_len)

    def _routes(self, sol):
        return self.parts.canonical(sol)

    def moves(self, sol):
        routes = self._routes(sol)
        n_routes = len(routes)
        seen = 0

        for i, route in enumerate(routes):
            L = len(route)
            for a in range(L):
                for b in range(a + 1, min(L, a + self.max_segment_len) + 1):
                    for j in range(n_routes + 1):
                        target_len = len(routes[j]) if j < n_routes else 0
                        for q in range(target_len + 1):
                            if j == i and q >= a and q <= b:
                                continue
                            mv = (i, a, b, j, q)
                            yield mv
                            seen += 1
                            if seen >= self.max_moves:
                                return

    def apply(self, sol, m):
        i, a, b, j, q = m
        routes = [list(r) for r in self._routes(sol)]
        segment = routes[i][a:b]
        del routes[i][a:b]
        if not routes[i]:
            del routes[i]
            if j > i:
                j -= 1
        if j == len(routes):
            routes.append(segment)
        else:
            if j == i and q > a:
                q -= (b - a)
            routes[j][q:q] = segment
        return self.parts.canonical(tuple(tuple(r) for r in routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    max_moves = params.get("max_moves", 200)
    max_segment_len = params.get("max_segment_len", 4)
    return RouteSegmentReinsertionNeighborhood(
        problem, max_moves=max_moves, max_segment_len=max_segment_len
    )
