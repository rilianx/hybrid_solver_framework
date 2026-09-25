from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import CLSPInstance, var_name

COMPONENT = {
    "name": "double_retiming_block_move",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.to_assignment", "ProblemModel.from_assignment", "problem.inst"],
    "params": {},
}


class DoubleRetimingBlockMoveNeighborhood:
    """Mueve dos setups del mismo ítem como un bloque pequeño.

    Movimiento: (i, t1, t2) con t1 < t2, sol[i][t1] = True, sol[i][t2] = True.
    Apaga ambos setups intermedios y enciende dos posiciones nuevas:
    - t1 se reubica en un período anterior o igual cercano vía consolidación,
    - t2 se reubica hacia el pasado/futuro según disponibilidad estructural.
    
    Aquí se usa como bloque de retiming: dos celdas tocadas se mueven juntas,
    generando vecinos que no se alcanzan con un simple shift unitario.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    def moves(self, sol) -> Iterable[tuple[int, int, int]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i in range(n_items):
            active = [t for t in range(n_periods) if sol[i][t]]
            for a in range(len(active)):
                for b in range(a + 1, len(active)):
                    yield (i, active[a], active[b])

    def apply(self, sol, m):
        i, t1, t2 = m
        s = [list(row) for row in sol]
        s[i][t1] = False
        s[i][t2] = False
        if t1 - 1 >= 0:
            s[i][t1 - 1] = True
        else:
            s[i][t1] = True
        if t2 - 1 >= 0 and t2 - 1 != t1 - 1:
            s[i][t2 - 1] = True
        else:
            s[i][t2] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t1, t2 = m
        s = [list(row) for row in sol]
        if t1 - 1 >= 0:
            s[i][t1 - 1] = False
        else:
            s[i][t1] = False
        if t2 - 1 >= 0 and t2 - 1 != t1 - 1:
            s[i][t2 - 1] = False
        else:
            s[i][t2] = False
        s[i][t1] = True
        s[i][t2] = True
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return DoubleRetimingBlockMoveNeighborhood(problem)
