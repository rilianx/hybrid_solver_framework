from functools import lru_cache


COMPONENT = {
    "name": "cross_item_period_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {},
}


class CrossItemPeriodSwapNeighborhood:
    """Intercambia el estado de setup entre dos ítems en un período dado: (i1, i2, t)."""

    def __init__(self, problem):
        self.problem = problem
        self._canonical = problem.parts.canonical
        self._objective = problem.objective
        # Caché acotada: muy útil cuando delta se llama varias veces sobre la misma solución.
        self._obj_cache = lru_cache(maxsize=8192)(self._objective)

    def moves(self, sol):
        n_items = len(sol)
        n_periods = len(sol[0]) if n_items else 0
        for i1 in range(n_items):
            row1 = sol[i1]
            for t1 in range(n_periods):
                if not row1[t1]:
                    continue
                for i2 in range(n_items):
                    row2 = sol[i2]
                    for t2 in range(n_periods):
                        if row2[t2]:
                            continue
                        if i1 != i2 or t1 != t2:
                            yield (i1, t1, i2, t2)

    def apply(self, sol, m):
        i1, t1, i2, t2 = m
        # Construcción inmutable directa, evitando listas intermedias y una segunda pasada.
        out = []
        for i, row in enumerate(sol):
            if i == i1:
                out.append(
                    tuple(
                        False if t == t1 else (True if (i == i2 and t == t2) else row[t])
                        for t in range(len(row))
                    )
                )
            elif i == i2:
                out.append(
                    tuple(
                        True if t == t2 else row[t]
                        for t in range(len(row))
                    )
                )
            else:
                out.append(tuple(row))
        return self._canonical(tuple(out))

    def delta(self, sol, m):
        # Evita recomputar objetivos repetidos; mantiene exactitud exacta.
        old = self._obj_cache(sol)
        new_sol = self.apply(sol, m)
        new = self._obj_cache(new_sol)
        return new - old


def build_component(problem, **params):
    return CrossItemPeriodSwapNeighborhood(problem)
