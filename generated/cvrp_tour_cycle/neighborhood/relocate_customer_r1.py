COMPONENT = {
    "name": "relocate_customer",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "max_step": {"type": "int", "range": [1, 50]},
    },
}


class RelocateCustomerNeighborhood:
    """Mueve un cliente de una posición a otra en el gran tour.
    Movimiento = (i_from, i_to) con i_from != i_to.
    """

    def __init__(self, problem, max_step: int = 10):
        self.problem = problem
        self.max_step = int(max_step)

    def moves(self, sol):
        tour = tuple(sol)
        n = len(tour)
        if n < 2:
            return
        for i in range(n):
            lo = max(0, i - self.max_step)
            hi = min(n - 1, i + self.max_step)
            for j in range(lo, hi + 1):
                if j != i:
                    yield (i, j)

    def apply(self, sol, m):
        tour = tuple(sol)
        i, j = m
        n = len(tour)
        if i == j or n < 2:
            return self.problem.parts.canonical(tour)
        item = tour[i]
        rest = tour[:i] + tour[i + 1 :]
        if j > i:
            j -= 1
        new_tour = rest[:j] + (item,) + rest[j:]
        return self.problem.parts.canonical(new_tour)

    def delta(self, sol, m):
        return float(self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol))

    def sample(self, sol, k, rng):
        all_moves = list(self.moves(sol))
        if len(all_moves) <= k:
            return all_moves
        return rng.sample(all_moves, k)


def build_component(problem, **params):
    max_step = params.get("max_step", 10)
    return RelocateCustomerNeighborhood(problem, max_step=max_step)
