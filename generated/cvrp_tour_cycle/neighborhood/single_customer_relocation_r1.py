from __future__ import annotations

from typing import Iterable
import random


COMPONENT = {
    "name": "single_customer_relocation",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "problem.parts.canonical"],
    "params": {},
}


class SingleCustomerRelocation:
    """Extrae un cliente de la posición i y lo inserta en la posición j.
    Movimiento: (i, j), con i != j; j se interpreta en el tour sin el elemento i.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[tuple[int, int]]:
        n = len(sol)
        for i in range(n):
            for j in range(n):
                if i != j:
                    yield (i, j)

    def apply(self, sol, m) -> tuple:
        i, j = m
        s = list(sol)
        c = s.pop(i)
        if j > i:
            j -= 1
        s.insert(j, c)
        return self.problem.parts.canonical(tuple(s))

    def undo(self, sol, m) -> tuple:
        i, j = m
        # Inversa exacta: mover el elemento actualmente en la posición j (post-movimiento)
        # de vuelta a la posición i original.
        s = list(sol)
        if j > i:
            # Tras el apply, el elemento original de i quedó en j-1.
            pos = j - 1
        else:
            pos = j
        c = s.pop(pos)
        s.insert(i, c)
        return self.problem.parts.canonical(tuple(s))

    def delta(self, sol, m) -> float:
        return float(self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol))


def build_component(problem, **params):
    return SingleCustomerRelocation(problem)
