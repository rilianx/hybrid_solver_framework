COMPONENT = {
    "name": "window_setup_compaction",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}

from typing import Iterable, Tuple
from examples.lotsizing.problem_model import var_name  # noqa: F401


Move = Tuple[int, int, int, Tuple[bool, ...]]


class WindowSetupCompactionNeighborhood:
    """Compacta una ventana temporal de un ítem preservando la información necesaria para deshacer."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[Move]:
        n_items = len(sol)
        n_periods = len(sol[0]) if n_items else 0
        for i in range(n_items):
            for a in range(n_periods):
                for b in range(a, n_periods):
                    # Guardamos el patrón original de la ventana para garantizar undo(apply(sol, m)) == sol.
                    yield (i, a, b, tuple(sol[i][a : b + 1]))

    def apply(self, sol, m):
        i, a, b, window = m
        compacted_window = list(window)
        if any(window):
            first_true = next(idx for idx, bit in enumerate(window) if bit)
            compacted_window = [False] * len(window)
            compacted_window[first_true] = True
        compacted_window = tuple(compacted_window)
        return tuple(
            tuple(
                compacted_window[tt - a] if ii == i and a <= tt <= b else bit
                for tt, bit in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def undo(self, sol, m):
        i, a, b, window = m
        return tuple(
            tuple(
                window[tt - a] if ii == i and a <= tt <= b else bit
                for tt, bit in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return WindowSetupCompactionNeighborhood(problem)
