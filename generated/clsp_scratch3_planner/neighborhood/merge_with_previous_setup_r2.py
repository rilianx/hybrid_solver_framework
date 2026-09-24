from __future__ import annotations

from typing import Iterable

from examples.lotsizing.problem_model import CLSPInstance, var_name  # noqa: F401


COMPONENT = {
    "name": "merge_with_previous_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class MergeWithPreviousSetup:
    """Vecindario que intenta fusionar lotes consecutivos del mismo ítem.

    Movimiento elemental: elegir un ítem i y un período t_cur con setup,
    localizar el último período anterior t_prev < t_cur donde ese mismo ítem
    también tenía setup, y proponer apagar el setup actual. El LP del problema
    decide entonces si la demanda se reacomoda al lote previo con mejor costo.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    def _last_previous_setup(self, sol, i: int, t: int):
        for tt in range(t - 1, -1, -1):
            if sol[i][tt]:
                return tt
        return None

    def moves(self, sol) -> Iterable[tuple[int, int, int]]:
        for i in range(self.inst.n_items):
            for t_cur in range(1, self.inst.n_periods):
                if not sol[i][t_cur]:
                    continue
                t_prev = self._last_previous_setup(sol, i, t_cur)
                if t_prev is None:
                    continue
                yield (i, t_prev, t_cur)

    def apply(self, sol, m):
        i, _t_prev, t_cur = m
        s = [list(row) for row in sol]
        s[i][t_cur] = False
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, _t_prev, t_cur = m
        s = [list(row) for row in sol]
        s[i][t_cur] = True
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return MergeWithPreviousSetup(problem)
