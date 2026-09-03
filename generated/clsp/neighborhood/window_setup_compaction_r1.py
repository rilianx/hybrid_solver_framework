COMPONENT = {
    "name": "window_setup_compaction",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}

from typing import Iterable
from examples.lotsizing.problem_model import var_name  # noqa: F401


class WindowSetupCompactionNeighborhood:
    """Compacta ventanas temporales de un ítem apagando setups intermedios y tardíos."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[tuple]:
        n_items = len(sol)
        n_periods = len(sol[0]) if n_items else 0
        for i in range(n_items):
            active_periods = [t for t in range(n_periods) if sol[i][t]]
            for a_idx, a in enumerate(active_periods):
                for b in active_periods[a_idx + 1:]:
                    # ventana [a, b]: se conserva el setup en a y se apagan los posteriores
                    yield (i, a, b)

    def apply(self, sol, m):
        i, a, b = m
        return tuple(
            tuple(
                (bit if ii != i or tt < a or tt > b else (tt == a))
                for tt, bit in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def undo(self, sol, m):
        i, a, b = m
        return tuple(
            tuple(
                (bit if ii != i or tt < a or tt > b else True)
                for tt, bit in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return WindowSetupCompactionNeighborhood(problem)
