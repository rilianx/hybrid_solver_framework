COMPONENT = {
    "name": "pairwise_customer_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "max_gap": {"type": "int", "range": [1, 50]},
    },
}


class PairwiseCustomerSwapNeighborhood:
    """Intercambia dos clientes del gran tour.
    Movimiento = (i, j) con i < j.
    """

    def __init__(self, problem, max_gap: int = 10):
        self.problem = problem
        self.max_gap = int(max_gap)

    def moves(self, sol):
        tour = tuple(sol)
        n = len(tour)
        if n < 2:
            return
        for i in range(n - 1):
            hi = min(n, i + 1 + self.max_gap)
            for j in range(i + 1, hi):
                yield (i, j)

    def apply(self, sol, m):
        tour = tuple(sol)
        i, j = m
        if i == j or len(tour) < 2:
            return self.problem.parts.canonical(tour)
        s = list(tour)
        s[i], s[j] = s[j], s[i]
        return self.problem.parts.canonical(tuple(s))

    def delta(self, sol, m):
        return float(self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol))

    def sample(self, sol, k, rng):
        all_moves = list(self.moves(sol))
        if len(all_moves) <= k:
            return all_moves
        return rng.sample(all_moves, k)


def build_component(problem, **params):
    max_gap = params.get("max_gap", 10)
    return PairwiseCustomerSwapNeighborhood(problem, max_gap=max_gap)
