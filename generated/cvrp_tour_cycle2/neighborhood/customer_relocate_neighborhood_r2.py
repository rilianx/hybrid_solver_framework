COMPONENT = {
    "name": "customer_relocate_neighborhood",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class CustomerRelocateNeighborhood:
    """Mueve un cliente de una posición a otra. Movimiento = (i, j), inserta sol[i] en j."""

    __slots__ = ("problem", "_obj_cache")

    def __init__(self, problem):
        self.problem = problem
        self._obj_cache = {}

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
        # Operación equivalente a pop(i) + insert(j), pero sin crear lista.
        s = sol if isinstance(sol, tuple) else tuple(sol)
        c = s[i]
        if j < i:
            return s[:j] + (c,) + s[j:i] + s[i + 1 :]
        # j > i
        return s[:i] + s[i + 1 : j] + (c,) + s[j:]

    def undo(self, sol, m):
        i, j = m
        if i == j:
            return tuple(sol)
        s = sol if isinstance(sol, tuple) else tuple(sol)
        # Inversa exacta de apply.
        if j < i:
            c = s[j]
            return s[:j] + s[j + 1 : i + 1] + (c,) + s[i + 1 :]
        # j > i
        c = s[j - 1]
        return s[:i] + (c,) + s[i:j - 1] + s[j:]

    def _objective(self, sol):
        try:
            return self._obj_cache[sol]
        except KeyError:
            val = self.problem.objective(sol)
            self._obj_cache[sol] = val
            return val

    def delta(self, sol, m):
        nxt = self.apply(sol, m)
        return self._objective(nxt) - self._objective(sol)


def build_component(problem, **params):
    return CustomerRelocateNeighborhood(problem)
