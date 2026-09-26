COMPONENT = {
    "name": "customer_swap_neighborhood",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class CustomerSwapNeighborhood:
    """Intercambio de dos clientes en la gran tour. Movimiento = (i, j) con i < j."""

    __slots__ = ("problem", "_obj_cache")

    def __init__(self, problem):
        self.problem = problem
        self._obj_cache = {}

    def moves(self, sol):
        n = len(sol)
        for i in range(n - 1):
            for j in range(i + 1, n):
                yield (i, j)

    def apply(self, sol, m):
        i, j = m
        s = list(sol)
        s[i], s[j] = s[j], s[i]
        return tuple(s)

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        base = self._obj_cache.get(sol)
        if base is None:
            base = self.problem.objective(sol)
            self._obj_cache[sol] = base

        neigh = self.apply(sol, m)
        val = self._obj_cache.get(neigh)
        if val is None:
            val = self.problem.objective(neigh)
            self._obj_cache[neigh] = val

        return val - base


def build_component(problem, **params):
    return CustomerSwapNeighborhood(problem)
