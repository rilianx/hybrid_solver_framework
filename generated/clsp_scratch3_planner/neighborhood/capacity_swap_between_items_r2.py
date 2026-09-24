from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import var_name  # noqa: F401  # requerido por contrato del problema


COMPONENT = {
    "name": "capacity_swap_between_items",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "window": {"type": "int", "range": [1, 3]},
        "max_moves": {"type": "int", "range": [1, 5000]},
    },
}


class CapacitySwapBetweenItems:
    """Vecindario de reasignación de setups entre períodos cercanos.

    Movimiento elemental: mover el setup de un ítem desde un período t a un
    período vecino u dentro de una ventana dada. Esto conserva la idea de
    liberar capacidad en períodos congestionados desplazando setups hacia
    períodos próximos con más holgura, y evita vaciar la vecindad cuando no
    existe un intercambio exacto disponible.
    """

    def __init__(self, problem, window: int = 1, max_moves: int = 5000):
        self.problem = problem
        self.window = window
        self.max_moves = max_moves

    def moves(self, sol) -> Iterable[tuple[int, int, int]]:
        inst = self.problem.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        yielded = 0

        # Enumeramos reubicaciones elementales de setups a períodos vecinos.
        for t in range(n_periods):
            for dt in range(1, self.window + 1):
                for u in (t - dt, t + dt):
                    if u < 0 or u >= n_periods:
                        continue
                    for i in range(n_items):
                        if sol[i][t] and not sol[i][u]:
                            yield (i, t, u)
                            yielded += 1
                            if yielded >= self.max_moves:
                                return

    def apply(self, sol, m):
        i, t_from, t_to = m
        s = [list(row) for row in sol]
        s[i][t_from] = False
        s[i][t_to] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t_from, t_to = m
        s = [list(row) for row in sol]
        s[i][t_to] = False
        s[i][t_from] = True
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    window = params.get("window", 1)
    max_moves = params.get("max_moves", 5000)
    return CapacitySwapBetweenItems(problem, window=window, max_moves=max_moves)
