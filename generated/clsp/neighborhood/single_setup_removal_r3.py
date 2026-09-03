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
    """Vecindario de eliminación/movimiento de setups para CLSP.

    La pieza mantiene la idea algorítmica original: explorar patrones con
    menos setups para que el LP recalcule producción e inventarios óptimos.

    Movimientos:
    - eliminar un setup activo que no sea el primer setup del ítem;
    - eliminar un bloque de dos setups consecutivos activos;
    - mover un setup activo un período hacia atrás, cuando exista un setup
      previo del mismo ítem, para favorecer consolidación y ahorro de setups.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[Tuple[int, int, int]]:
        n_periods = len(sol[0]) if sol else 0

        for i, row in enumerate(sol):
            active_periods = [t for t, active in enumerate(row) if active]
            if not active_periods:
                continue

            first_active = active_periods[0]

            # 1) Eliminar setups "interiores" o no iniciales: suele permitir
            # que el inventario del LP cubra la demanda con menos setups.
            for t in active_periods[1:]:
                yield (i, t, t)

            # 2) Eliminar dos setups consecutivos activos.
            for t in range(n_periods - 1):
                if row[t] and row[t + 1]:
                    yield (i, t, t + 1)

            # 3) Mover un setup hacia atrás para consolidar producción.
            #    Representación: (i, t_from, t_to) con t_to < t_from.
            #    Solo proponemos movimientos hacia un período previo activo,
            #    que es donde típicamente se obtiene mejora desde lot-for-lot.
            for t in active_periods[1:]:
                prev_candidates = [u for u in active_periods if u < t]
                if prev_candidates:
                    u = prev_candidates[-1]
                    if u != t:
                        yield (i, t, u)

            # 4) También permitimos retirar el último setup si existe uno previo:
            #    desde lot-for-lot es el caso más habitual de mejora.
            if len(active_periods) >= 2:
                last_active = active_periods[-1]
                if last_active != first_active:
                    yield (i, last_active, last_active)

    def apply(self, sol, m):
        i, t0, t1 = m

        # Caso 1: eliminación pura de un periodo o bloque [t0, t1]
        if t0 == t1:
            return tuple(
                tuple(
                    False if ii == i and tt == t0 else bit
                    for tt, bit in enumerate(row)
                )
                for ii, row in enumerate(sol)
            )

        # Caso 2: movimiento de setup de t0 a t1 (t1 < t0)
        new_sol = []
        for ii, row in enumerate(sol):
            if ii != i:
                new_sol.append(tuple(row))
                continue

            new_row = []
            for tt, bit in enumerate(row):
                if tt == t0:
                    new_row.append(False)
                elif tt == t1:
                    new_row.append(True)
                else:
                    new_row.append(bit)
            new_sol.append(tuple(new_row))

        return tuple(new_sol)

    def undo(self, sol, m):
        i, t0, t1 = m

        # Inverso del borrado: reactivar exactamente el/los periodos borrados.
        if t0 == t1:
            return tuple(
                tuple(
                    True if ii == i and tt == t0 else bit
                    for tt, bit in enumerate(row)
                )
                for ii, row in enumerate(sol)
            )

        # Inverso del movimiento t0 -> t1: restituir setup en t0 y quitar en t1.
        new_sol = []
        for ii, row in enumerate(sol):
            if ii != i:
                new_sol.append(tuple(row))
                continue

            new_row = []
            for tt, bit in enumerate(row):
                if tt == t0:
                    new_row.append(True)
                elif tt == t1:
                    new_row.append(False)
                else:
                    new_row.append(bit)
            new_sol.append(tuple(new_row))

        return tuple(new_sol)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return SingleSetupRemovalNeighborhood(problem)
