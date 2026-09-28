COMPONENT = {
    "name": "customer_relocate_neighborhood",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class CustomerRelocateNeighborhood:
    """Mueve un cliente de una posición a otra. Movimiento = (i, j), inserta sol[i] en j."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol):
        n = len(sol)
        for i in range(n):
            for j in range(n):
                if i != j:
                    yield (i, j)

    def apply(self, sol, m):
        i, j = m
        if i == j:
            return tuple(sol)
        s = list(sol)
        c = s.pop(i)
        if j > i:
            j -= 1
        s.insert(j, c)
        return tuple(s)

    def undo(self, sol, m):
        i, j = m
        if i == j:
            return tuple(sol)
        s = list(sol)
        c = s.pop(j if j < i else j - 1)
        s.insert(i, c)
        return tuple(s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CustomerRelocateNeighborhood(problem)
