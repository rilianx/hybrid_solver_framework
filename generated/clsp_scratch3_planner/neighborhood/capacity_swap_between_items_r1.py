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
    """Intercambia setups entre dos ítems en períodos adyacentes para aliviar congestión.

    Movimiento = (i, j, t_from, t_to), donde se intercambia la presencia de
    setup de i y j entre los períodos t_from y t_to.
    """

    def __init__(self, problem, window: int = 1, max_moves: int = 5000):
        self.problem = problem
        self.window = window
        self.max_moves = max_moves

    def moves(self, sol) -> Iterable[tuple[int, int, int, int]]:
        inst = self.problem.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        yielded = 0

        # Priorizamos pares adyacentes: el caso "vecino con más holgura" suele ser t±1.
        for t in range(n_periods):
            for dt in range(1, self.window + 1):
                for u in (t - dt, t + dt):
                    if u < 0 or u >= n_periods:
                        continue

                    # i: setup en t y no en u
                    # j: setup en u y no en t
                    for i in range(n_items):
                        if not sol[i][t] or sol[i][u]:
                            continue
                        for j in range(n_items):
                            if i == j:
                                continue
                            if sol[j][t] or not sol[j][u]:
                                continue
                            m = (i, j, t, u)
                            yield m
                            yielded += 1
                            if yielded >= self.max_moves:
                                return

    def apply(self, sol, m):
        i, j, t_from, t_to = m
        s = [list(row) for row in sol]
        s[i][t_from] = False
        s[i][t_to] = True
        s[j][t_to] = False
        s[j][t_from] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        # El movimiento es involutivo: aplicar de nuevo restaura la solución.
        return self.apply(sol, m)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    window = params.get("window", 1)
    max_moves = params.get("max_moves", 5000)
    return CapacitySwapBetweenItems(problem, window=window, max_moves=max_moves)
