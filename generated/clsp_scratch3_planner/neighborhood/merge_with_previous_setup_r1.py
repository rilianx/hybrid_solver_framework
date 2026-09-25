from __future__ import annotations

from typing import Iterable, Protocol, Any
from dataclasses import dataclass

from examples.lotsizing.problem_model import CLSPInstance, var_name  # noqa: F401


COMPONENT = {
    "name": "merge_with_previous_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class MergeWithPreviousSetup:
    """Fusiona un lote con el último setup previo del mismo ítem apagando el setup actual.

    Movimiento = (i, t_prev, t_cur), donde t_prev < t_cur y ambos son períodos con setup
    del ítem i. La aplicación apaga el setup en t_cur; el LP de evaluación redistribuye
    la producción, intentando trasladar la demanda de t_cur al lote previo.
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
        # Generamos solo movimientos que realmente mejoran para cumplir el contrato
        # del vecindario útil en la solución de partida.
        for i in range(self.inst.n_items):
            for t_cur in range(1, self.inst.n_periods):
                if not sol[i][t_cur]:
                    continue
                t_prev = self._last_previous_setup(sol, i, t_cur)
                if t_prev is None:
                    continue
                m = (i, t_prev, t_cur)
                if self.delta(sol, m) < -1e-9:
                    yield m

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
