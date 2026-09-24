from typing import Iterable


COMPONENT = {
    "name": "drop_redundant_late_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class DropRedundantLateSetup:
    """Elimina un setup tardío de un ítem cuando ya existe un setup previo.

    Movimiento:
      - ("drop", i, t): pone sol[i][t] := False si ese setup es redundante.
      - ("noop", 0, 0): movimiento de reserva para garantizar no vaciedad
        cuando no hay setups redundantes disponibles.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol):
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        found = False
        for i in range(n_items):
            seen_setup = False
            for t in range(n_periods):
                if sol[i][t]:
                    if seen_setup:
                        found = True
                        yield ("drop", i, t)
                    else:
                        seen_setup = True

        if not found and n_items > 0 and n_periods > 0:
            yield ("noop", 0, 0)

    def apply(self, sol, m):
        kind, i, t = m
        if kind == "noop":
            return tuple(tuple(row) for row in sol)

        return tuple(
            tuple(
                sol[ii][tt] if (ii != i or tt != t) else False
                for tt in range(self.inst.n_periods)
            )
            for ii in range(self.inst.n_items)
        )

    def undo(self, sol, m):
        kind, i, t = m
        if kind == "noop":
            return tuple(tuple(row) for row in sol)

        return tuple(
            tuple(
                sol[ii][tt] if (ii != i or tt != t) else True
                for tt in range(self.inst.n_periods)
            )
            for ii in range(self.inst.n_items)
        )

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return DropRedundantLateSetup(problem)
