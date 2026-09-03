from __future__ import annotations

from typing import Iterable, Tuple, Union
from examples.lotsizing.problem_model import LotSizingModel


COMPONENT = {
    "name": "same_period_setup_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}

Move = Tuple[str, int, int, int]  # ("off"|"swap", t, i_out, i_in)


class SamePeriodSetupSwap:
    """Vecindario simple por período.

    Incluye:
    - apagado elemental de un setup activo: ("off", t, i, -1)
    - intercambio dentro del mismo período: ("swap", t, i_out, i_in)

    Esto mantiene la idea original de trabajar dentro del mismo período,
    pero añade movimientos elementales que sí pueden mejorar desde la solución
    inicial de partida.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[Move]:
        inst = self.problem.inst
        n_items = inst.n_items
        n_periods = inst.n_periods

        for t in range(n_periods):
            active = [i for i in range(n_items) if sol[i][t]]
            inactive = [i for i in range(n_items) if not sol[i][t]]

            # Movimiento elemental: apagar un setup activo.
            for i in active:
                yield ("off", t, i, -1)

            # Movimiento original: swap dentro del mismo período.
            for i_out in active:
                for i_in in inactive:
                    yield ("swap", t, i_out, i_in)

    def apply(self, sol, m):
        kind, t, i1, i2 = m
        s = [list(r) for r in sol]

        if kind == "off":
            s[i1][t] = False
        elif kind == "swap":
            s[i1][t] = False
            s[i2][t] = True
        else:
            raise ValueError(f"Unknown move kind: {kind}")

        return tuple(tuple(r) for r in s)

    def undo(self, sol, m):
        kind, t, i1, i2 = m
        s = [list(r) for r in sol]

        if kind == "off":
            s[i1][t] = True
        elif kind == "swap":
            s[i1][t] = True
            s[i2][t] = False
        else:
            raise ValueError(f"Unknown move kind: {kind}")

        return tuple(tuple(r) for r in s)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return SamePeriodSetupSwap(problem)
