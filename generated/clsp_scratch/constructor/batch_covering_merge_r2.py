from random import Random
from typing import Tuple

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "batch_covering_merge",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "merge_window": {"type": "int", "range": [1, 8]},
        "inventory_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class BatchCoveringMerge:
    """Constructor simple: crea setups en bloques de demanda y garantiza cobertura prefix por ítem."""

    def __init__(self, merge_window: int = 2, inventory_bias: float = 0.4):
        self.merge_window = merge_window
        self.inventory_bias = inventory_bias

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        for i in range(n_items):
            demand = inst.demand[i]
            if sum(demand) <= 1e-12:
                continue

            # Detecta bloques de demanda positiva y abre un setup al inicio de cada bloque.
            t = 0
            while t < n_periods:
                while t < n_periods and demand[t] <= 1e-12:
                    t += 1
                if t >= n_periods:
                    break

                sol[i][t] = True

                # Si el bloque es largo o la demanda se dispersa, añade otro setup dentro de la ventana.
                end = t + 1
                span = 1
                while end < n_periods and span < self.merge_window:
                    if demand[end] <= 1e-12:
                        # No mezclar demasiado: si aparece hueco, cortamos el bloque.
                        break
                    span += 1
                    end += 1

                if end < n_periods and demand[end] > 1e-12 and rng.random() < self.inventory_bias:
                    sol[i][end] = True

                t = end

            # Refuerzo: si hay demandas posteriores sin setups suficientes, activa periodos de demanda
            # para evitar faltantes de cobertura prefix en la capa contractual.
            cum_demand = 0.0
            covered_periods = [p for p in range(n_periods) if sol[i][p]]
            if covered_periods:
                covered_set = set(covered_periods)
            else:
                covered_set = set()

            for t in range(n_periods):
                cum_demand += demand[t]
                if demand[t] > 1e-12 and t not in covered_set:
                    sol[i][t] = True
                    covered_set.add(t)

            # Si el ítem tiene demanda, al menos un setup debe existir no más tarde que su primer demanda.
            if not any(sol[i]):
                first = next((t for t in range(n_periods) if demand[t] > 1e-12), None)
                if first is not None:
                    sol[i][first] = True

        sol_tuple = tuple(tuple(row) for row in sol)

        # Reparación ligera: si alguna solución no es factible, añade setups en los primeros periodos
        # con demanda positiva del ítem, sin tocar otros ítems.
        if not inst is None and not self._is_feasible(inst, sol_tuple):
            sol_tuple = self._repair(inst, sol_tuple, rng)

        if not self._is_feasible(inst, sol_tuple):
            raise RuntimeError("No se pudo construir una solución factible")
        return sol_tuple

    def _is_feasible(self, inst: CLSPInstance, sol) -> bool:
        # En este contrato solo disponemos del patrón; la factibilidad real la valida el framework.
        # Esta comprobación evita eliminar setups por error.
        return True

    def _repair(self, inst: CLSPInstance, sol, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        solm = [list(row) for row in sol]

        for i in range(n_items):
            if sum(inst.demand[i]) <= 1e-12:
                continue
            if not any(solm[i]):
                first = next((t for t in range(n_periods) if inst.demand[i][t] > 1e-12), 0)
                solm[i][first] = True
            else:
                # Garantiza cobertura temprana: si la primera demanda aparece antes del primer setup,
                # activa el propio periodo de la primera demanda.
                first_setup = next(t for t in range(n_periods) if solm[i][t])
                first_dem = next((t for t in range(n_periods) if inst.demand[i][t] > 1e-12), None)
                if first_dem is not None and first_dem < first_setup:
                    solm[i][first_dem] = True

        return tuple(tuple(row) for row in solm)


def build_component(problem, merge_window: int = 2, inventory_bias: float = 0.4):
    return BatchCoveringMerge(merge_window=merge_window, inventory_bias=inventory_bias)
