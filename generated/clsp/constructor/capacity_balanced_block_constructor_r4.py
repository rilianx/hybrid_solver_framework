from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "capacity_balanced_block_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "randomness": {"type": "float", "range": [0.0, 1.0]},
        "late_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class CapacityBalancedBlockConstructor:
    """Constructor por bloques: activa setups en los períodos con demanda."""

    def __init__(self, randomness: float = 0.25, late_bias: float = 0.4):
        self.randomness = randomness
        self.late_bias = late_bias

    def _sol_from_assign(self, assign: List[List[bool]]) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(tuple(row) for row in assign)

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods

        # Heurística conservadora: garantizar cobertura activando setup en todo período con demanda positiva.
        # Esto evita backlog y deja al LP de cantidades distribuir la producción.
        y = [[False] * n_periods for _ in range(n_items)]

        item_order = list(range(n_items))
        first_demand = []
        total_demand = []
        for i in range(n_items):
            fd = next((t for t in range(n_periods) if inst.demand[i][t] > 0), n_periods - 1)
            first_demand.append(fd)
            total_demand.append(sum(inst.demand[i]))

        # Orden estable: ítems con demanda más temprana y mayor intensidad primero.
        item_order.sort(
            key=lambda i: (
                first_demand[i],
                -(total_demand[i] + 1.0) / max(float(inst.setup_cost[i]), 1.0),
                -float(inst.setup_time[i]),
                i,
            )
        )

        for i in item_order:
            demand_periods = [t for t in range(n_periods) if inst.demand[i][t] > 0]
            if not demand_periods:
                continue

            # Activamos setup en cada período con demanda positiva.
            # El parámetro late_bias se usa solo para romper empates cuando se eligen refuerzos extra.
            for t in demand_periods:
                y[i][t] = True

            # Refuerzo opcional: si hay mucha demanda concentrada al final, añadir setups tempranos
            # para permitir almacenar producción y repartir carga temporalmente.
            if self.randomness > 0.0 and rng.random() < self.randomness:
                early_t = demand_periods[0]
                late_t = demand_periods[-1]
                if late_bias := self.late_bias:
                    if late_t > early_t and rng.random() < late_bias * 0.25:
                        y[i][early_t] = True

        candidate = self._sol_from_assign(y)

        # Reparación ligera si existe el modelo problema ligado.
        if hasattr(inst, "problem"):
            problem = inst.problem
            if problem.is_feasible(candidate):
                return candidate

            # Si por alguna razón sigue siendo infactible, intentamos reforzar con setups adicionales
            # en períodos más tempranos para los ítems con demanda más urgente.
            for i in item_order:
                demand_periods = [t for t in range(n_periods) if inst.demand[i][t] > 0]
                if not demand_periods:
                    continue
                for t in range(demand_periods[0], -1, -1):
                    if not y[i][t]:
                        trial = [row[:] for row in y]
                        trial[i][t] = True
                        trial_sol = self._sol_from_assign(trial)
                        if problem.is_feasible(trial_sol):
                            return trial_sol
                        y = trial
                        candidate = trial_sol

            if problem.is_feasible(candidate):
                return candidate

        return candidate


def build_component(problem, randomness: float = 0.25, late_bias: float = 0.4):
    return CapacityBalancedBlockConstructor(randomness=randomness, late_bias=late_bias)
