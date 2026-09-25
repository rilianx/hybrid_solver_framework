from __future__ import annotations

from typing import Iterable

COMPONENT = {
    "name": "shift_setup_to_adjacent_period",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "direction": {"type": "cat", "values": ["both", "left", "right"]},
        "window": {"type": "int", "range": [1, 4]},
    },
}


class ShiftSetupToAdjacentPeriodNeighborhood:
    """Mueve un setup de un período a un vecino temporal adyacente del mismo ítem."""

    def __init__(self, problem, direction: str = "both", window: int = 1):
        self.problem = problem
        self.inst = problem.inst
        self.direction = direction
        self.window = window

    def moves(self, sol) -> Iterable[tuple[int, int, int]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                for dt in range(1, self.window + 1):
                    if self.direction in ("both", "left") and t - dt >= 0:
                        t_to = t - dt
                        if not sol[i][t_to]:
                            yield (i, t, t_to)
                    if self.direction in ("both", "right") and t + dt < n_periods:
                        t_to = t + dt
                        if not sol[i][t_to]:
                            yield (i, t, t_to)

    def apply(self, sol, m):
        i, t_from, t_to = m
        s = [list(row) for row in sol]
        s[i][t_from] = False
        s[i][t_to] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t_from, t_to = m
        return self.apply(sol, (i, t_to, t_from))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, direction: str = "both", window: int = 1):
    return ShiftSetupToAdjacentPeriodNeighborhood(problem, direction=direction, window=window)
