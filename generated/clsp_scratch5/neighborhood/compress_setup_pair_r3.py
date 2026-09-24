from __future__ import annotations

COMPONENT = {
    "name": "compress_setup_pair",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class CompressSetupPair:
    """Vecindario elemental sobre setups.

    Movimiento = (i, t): desactiva un setup individual.
    Se mantiene la idea de "compresión" al explorar la eliminación de setups
    activos, dejando al evaluador LP reoptimizar cantidades e inventarios.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol):
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i in range(n_items):
            for t in range(n_periods):
                if sol[i][t]:
                    yield (i, t)

    def apply(self, sol, m):
        i, t = m
        return tuple(
            tuple(
                (not sol[ii][tt] if (ii == i and tt == t) else sol[ii][tt])
                for tt in range(self.inst.n_periods)
            )
            for ii in range(self.inst.n_items)
        )

    def undo(self, sol, m):
        i, t = m
        return tuple(
            tuple(
                (not sol[ii][tt] if (ii == i and tt == t) else sol[ii][tt])
                for tt in range(self.inst.n_periods)
            )
            for ii in range(self.inst.n_items)
        )

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CompressSetupPair(problem)
