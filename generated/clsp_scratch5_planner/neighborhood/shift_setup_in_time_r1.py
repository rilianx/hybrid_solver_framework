from typing import Iterable, Tuple
from examples.lotsizing.problem_model import Solution, Move  # type: ignore

COMPONENT = {
    "name": "shift_setup_in_time",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class ShiftSetupInTime:
    """Desplaza un setup activo de un ítem a un período vecino (t-1 o t+1).

    Movimiento:
        (i, t, direction)

    donde direction = -1 significa mover de t a t-1, y direction = +1 de t a t+1.
    Solo se generan movimientos si el período vecino existe y está apagado, para
    preservar el número de setups del ítem.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol: Solution) -> Iterable[Move]:
        n_periods = self.inst.n_periods
        for i, row in enumerate(sol):
            for t, active in enumerate(row):
                if not active:
                    continue
                if t > 0 and not row[t - 1]:
                    yield (i, t, -1)
                if t + 1 < n_periods and not row[t + 1]:
                    yield (i, t, +1)

    def apply(self, sol: Solution, m: Move) -> Solution:
        i, t, direction = m
        t2 = t + direction
        rows = [list(r) for r in sol]
        rows[i][t] = False
        rows[i][t2] = True
        return tuple(tuple(r) for r in rows)

    def undo(self, sol: Solution, m: Move) -> Solution:
        i, t, direction = m
        t2 = t + direction
        rows = [list(r) for r in sol]
        rows[i][t] = True
        rows[i][t2] = False
        return tuple(tuple(r) for r in rows)

    def delta(self, sol: Solution, m: Move) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return ShiftSetupInTime(problem)
