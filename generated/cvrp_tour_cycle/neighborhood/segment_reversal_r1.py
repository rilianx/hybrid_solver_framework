COMPONENT = {
    "name": "segment_reversal",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "max_len": {"type": "int", "range": [2, 100]},
    },
}


class SegmentReversalNeighborhood:
    """Invierte un segmento contiguo del gran tour.
    Movimiento = (i, j) con 0 <= i < j < n; aplica 2-opt sobre la secuencia.
    """

    def __init__(self, problem, max_len: int = 20):
        self.problem = problem
        self.max_len = int(max_len)

    def moves(self, sol):
        tour = tuple(sol)
        n = len(tour)
        if n < 2:
            return
        for i in range(n - 1):
            hi = min(n, i + self.max_len)
            for j in range(i + 1, hi):
                yield (i, j)

    def apply(self, sol, m):
        tour = tuple(sol)
        i, j = m
        if i >= j or len(tour) < 2:
            return self.problem.parts.canonical(tour)
        new_tour = tour[:i] + tuple(reversed(tour[i : j + 1])) + tour[j + 1 :]
        return self.problem.parts.canonical(new_tour)

    def delta(self, sol, m):
        return float(self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol))

    def sample(self, sol, k, rng):
        all_moves = list(self.moves(sol))
        if len(all_moves) <= k:
            return all_moves
        return rng.sample(all_moves, k)


def build_component(problem, **params):
    max_len = params.get("max_len", 20)
    return SegmentReversalNeighborhood(problem, max_len=max_len)
