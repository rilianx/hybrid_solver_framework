from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance, var_name


COMPONENT = {
    "name": "backward_capacity_lot_builder",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class BackwardCapacityLotBuilder:
    """Construye lotes hacia atrás: agrupa demanda contigua y la coloca en períodos con holgura."""

    def __init__(self):
        pass

    def _empty_sol(self, inst: CLSPInstance):
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set_true(self, sol, i: int, t: int):
        return tuple(
            tuple((tt == t) or row[tt] for tt in range(len(row))) if ii == i else row
            for ii, row in enumerate(sol)
        )

    def _build_greedy(self, inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        n, T = inst.n_items, inst.n_periods
        cap_left = [float(c) for c in inst.capacity]
        sol = [[False] * T for _ in range(n)]

        # Construye lotes de cada ítem de derecha a izquierda y los asigna al
        # período más tardío posible con capacidad residual suficiente.
        for i in range(n):
            t = T - 1
            while t >= 0:
                if inst.demand[i][t] <= 1e-9:
                    t -= 1
                    continue

                load = inst.setup_time[i]
                p = t
                while p > 0:
                    candidate = load + sum(inst.demand[i][k] for k in range(p - 1, t + 1))
                    if candidate <= cap_left[p - 1] + 1e-9:
                        p -= 1
                        load = candidate
                    else:
                        break

                # Si el bloque no cabe en p, lo partimos y fijamos el bloque más corto posible.
                while p <= t:
                    block = inst.setup_time[i] + sum(inst.demand[i][k] for k in range(p, t + 1))
                    if block <= cap_left[p] + 1e-9:
                        sol[i][p] = True
                        cap_left[p] -= block
                        break
                    t -= 1
                    if t < 0:
                        break
                    p = t
                t -= 1

        return tuple(tuple(row) for row in sol)

    def _repair(self, problem, inst: CLSPInstance, sol):
        # Reparación conservadora: si no es factible, abre setups adicionales
        # en períodos previos donde todavía haya holgura.
        if problem.is_feasible(sol):
            return sol

        n, T = inst.n_items, inst.n_periods
        current = [list(row) for row in sol]

        for _ in range(n * T * 2):
            if problem.is_feasible(tuple(tuple(r) for r in current)):
                return tuple(tuple(r) for r in current)

            improved = False
            # Intenta activar un setup en un período anterior para dar más margen al LP.
            for i in range(n):
                for t in range(T):
                    if inst.demand[i][t] <= 1e-9:
                        continue
                    for p in range(t, -1, -1):
                        if not current[i][p]:
                            trial = [row[:] for row in current]
                            trial[i][p] = True
                            trial_sol = tuple(tuple(r) for r in trial)
                            if problem.objective(trial_sol) <= problem.objective(tuple(tuple(r) for r in current)) + 1e-9:
                                current = trial
                                improved = True
                                break
                    if improved:
                        break
                if improved:
                    break
            if not improved:
                break

        return tuple(tuple(r) for r in current)

    def build(self, inst: CLSPInstance, rng: Random):
        # La aleatoriedad solo se usa para desempates suaves en la reparación.
        sol = self._build_greedy(inst)
        return self._repair(_problem_proxy(inst), inst, sol)


def _problem_proxy(inst):
    # Proxy mínimo: build() requiere problem.is_feasible/objective; se inyecta desde build_component.
    raise RuntimeError("internal proxy should be replaced in build_component")


def build_component(problem, **params):
    class _B(BackwardCapacityLotBuilder):
        def build(self, inst: CLSPInstance, rng: Random):
            sol = self._build_greedy(inst)
            return self._repair(problem, inst, sol)

    return _B()
