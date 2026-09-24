COMPONENT = {
    "name": "compress_setup_triple",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class CompressSetupTriple:
    """Vecindario elemental sobre setups: alterna un único setup (i, t).

    Se mantiene la idea de explorar la compresión del patrón de setups,
    pero con movimientos atómicos y con undo exacto.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol):
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i in range(n_items):
            for t in range(n_periods):
                yield (i, t)

    def apply(self, sol, m):
        i, t = m
        return tuple(
            tuple(
                (not sol[ii][tt]) if (ii == i and tt == t) else sol[ii][tt]
                for tt in range(self.inst.n_periods)
            )
            for ii in range(self.inst.n_items)
        )

    def undo(self, sol, m):
        # El mismo movimiento es su propio inverso: alterna un único bit.
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CompressSetupTriple(problem)
