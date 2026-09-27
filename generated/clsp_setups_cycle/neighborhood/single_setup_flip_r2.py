from collections import OrderedDict


COMPONENT = {
    "name": "single_setup_flip",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {},
}


class SingleSetupFlipNeighborhood:
    """Vecindario bit-flip: activa o desactiva un único setup (i, t)."""

    _OBJ_CACHE_SIZE = 8192

    def __init__(self, problem):
        self.problem = problem
        self._obj_cache = OrderedDict()
        self._last_sol = None
        self._last_obj = None
        inst = problem.inst
        self._n_items = inst.n_items
        self._n_periods = inst.n_periods

    def _objective_cached(self, sol):
        cached = self._obj_cache.get(sol)
        if cached is not None:
            self._obj_cache.move_to_end(sol)
            return cached
        val = self.problem.objective(sol)
        self._obj_cache[sol] = val
        self._obj_cache.move_to_end(sol)
        if len(self._obj_cache) > self._OBJ_CACHE_SIZE:
            self._obj_cache.popitem(last=False)
        return val

    def moves(self, sol):
        n_items = len(sol)
        n_periods = len(sol[0]) if n_items else 0
        for i in range(n_items):
            for t in range(n_periods):
                yield (i, t)

    def apply(self, sol, m):
        i, t = m
        s = [list(row) for row in sol]
        s[i][t] = not s[i][t]
        return self.problem.parts.canonical(tuple(tuple(row) for row in s))

    def delta(self, sol, m):
        # Cachea la evaluación de la solución base; el vecino sigue evaluándose exactamente.
        if sol == self._last_sol:
            base = self._last_obj
        else:
            base = self._objective_cached(sol)
            self._last_sol = sol
            self._last_obj = base

        neighbor = self.apply(sol, m)
        return self._objective_cached(neighbor) - base


def build_component(problem, **params):
    return SingleSetupFlipNeighborhood(problem)
