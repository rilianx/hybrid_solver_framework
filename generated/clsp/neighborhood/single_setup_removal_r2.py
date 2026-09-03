COMPONENT = {
    "name": "single_setup_removal",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}

from typing import Iterable, Tuple
from examples.lotsizing.problem_model import var_name  # noqa: F401


class SingleSetupRemovalNeighborhood:
    """Vecindario de eliminación de setups.

    Genera movimientos de:
    - eliminación de un único setup activo;
    - eliminación de dos setups activos consecutivos del mismo ítem.

    La idea es permitir que el LP asociado reubique producción e inventario
    para cubrir demanda con menos setups cuando sea conveniente.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[Tuple[int, int, int]]:
        n_periods = len(sol[0]) if sol else 0

        for i, row in enumerate(sol):
            # Eliminación de un único setup
            for t, active in enumerate(row):
                if active:
                    yield (i, t, t)

            # Eliminación de dos setups consecutivos activos
            for t in range(n_periods - 1):
                if row[t] and row[t + 1]:
                    yield (i, t, t + 1)

    def apply(self, sol, m):
        i, t0, t1 = m
        return tuple(
            tuple(
                bit if ii != i or not (t0 <= tt <= t1) else False
                for tt, bit in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def undo(self, sol, m):
        i, t0, t1 = m
        return tuple(
            tuple(
                (not bit) if ii == i and t0 <= tt <= t1 else bit
                for tt, bit in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return SingleSetupRemovalNeighborhood(problem)
