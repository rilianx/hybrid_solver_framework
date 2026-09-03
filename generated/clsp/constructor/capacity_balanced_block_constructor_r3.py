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
    """Constructor por bloques: coloca setups en bloques de demanda, balanceando capacidad."""

    def __init__(self, randomness: float = 0.25, late_bias: float = 0.4):
        self.randomness = randomness
        self.late_bias = late_bias

    def _sol_from_assign(self, n_items: int, n_periods: int, assign: List[List[bool]]) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(tuple(row) for row in assign)

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods

        # Construimos por ítem bloques de demanda positiva.
        # Cada bloque arranca en un período con demanda y se mantiene mientras
        # la demanda acumulada que debe cubrir ese bloque sea razonable para una sola activación.
        y = [[False] * n_periods for _ in range(n_items)]

        item_order = list(range(n_items))
        first_demand = []
        total_demand = []
        for i in range(n_items):
            fd = next((t for t in range(n_periods) if inst.demand[i][t] > 0), n_periods - 1)
            first_demand.append(fd)
            total_demand.append(sum(inst.demand[i]))

        item_order.sort(
            key=lambda i: (
                first_demand[i],
                -(total_demand[i] + 1.0) / max(inst.setup_cost[i], 1.0),
                -inst.setup_time[i],
                i,
            )
        )

        # Capacidad disponible para producción después de setups.
        remaining = [float(inst.capacity[t]) for t in range(n_periods)]

        for i in item_order:
            # Períodos con demanda estrictamente positiva.
            demand_periods = [t for t in range(n_periods) if inst.demand[i][t] > 0]
            if not demand_periods:
                # Si no hay demanda, no hace falta producir este ítem.
                continue

            # Capacidad "aproximada" que puede absorber un bloque arrancando en un período.
            # Si la demanda acumulada del bloque supera lo que parece caber, se abre un nuevo bloque.
            block_start = demand_periods[0]
            block_acc = 0.0

            for idx, t in enumerate(demand_periods):
                d = float(inst.demand[i][t])

                if not y[i][block_start]:
                    y[i][block_start] = True
                    remaining[block_start] -= float(inst.setup_time[i])

                # Sesgo aleatorio para abrir bloques un poco antes o después cuando sea posible.
                # Solo afecta la partición interna, nunca deja una demanda sin cobertura.
                if idx > 0 and self.randomness > 0.0 and rng.random() < self.randomness * 0.15:
                    # Intentamos abrir un nuevo bloque en el período actual si hay margen.
                    tentative_start = t
                    if not y[i][tentative_start]:
                        y[i][tentative_start] = True
                        remaining[tentative_start] -= float(inst.setup_time[i])
                        block_start = tentative_start
                        block_acc = 0.0

                block_acc += d

                # Si el bloque ya creció demasiado para ser razonablemente servido por una sola activación,
                # cerramos y reabrimos en el siguiente período con demanda.
                # Usamos una cota conservadora: capacidad del período de arranque menos setup.
                start_capacity = float(inst.capacity[block_start]) - float(inst.setup_time[i])
                if idx + 1 < len(demand_periods):
                    next_t = demand_periods[idx + 1]
                    # Si el hueco temporal es largo o la demanda acumulada es alta, abrimos nuevo bloque.
                    if block_acc > max(0.0, start_capacity) or next_t > t + 1:
                        block_start = next_t
                        block_acc = 0.0
                        if not y[i][block_start]:
                            y[i][block_start] = True
                            remaining[block_start] -= float(inst.setup_time[i])

            # Si quedó solo un bloque con demanda muy grande, agregamos refuerzos en períodos con demanda
            # posteriores para no dejar toda la carga en una única producción.
            # Esto mantiene movimientos elementales: solo activaciones simples de setup.
            if len(demand_periods) >= 2:
                avg_load = total_demand[i] / float(len(demand_periods))
                for t in demand_periods[1:]:
                    if avg_load > max(1.0, float(inst.capacity[t]) * 0.75) and not y[i][t]:
                        y[i][t] = True
                        remaining[t] -= float(inst.setup_time[i])

        candidate = self._sol_from_assign(n_items, n_periods, y)

        # Reparación ligera si la instancia ligada expone el problema.
        if hasattr(inst, "problem"):
            problem = inst.problem
            if problem.is_feasible(candidate):
                return candidate

            # 1) Añadimos setups en períodos de demanda no cubiertos para los ítems más urgentes.
            # 2) Preferimos períodos más tempranos para respetar el no-backlog.
            for _ in range(n_items * n_periods):
                if problem.is_feasible(candidate):
                    return candidate

                improved = False
                for i in item_order:
                    demand_periods = [t for t in range(n_periods) if inst.demand[i][t] > 0]
                    for t in demand_periods:
                        if not y[i][t]:
                            trial = [row[:] for row in y]
                            trial[i][t] = True
                            trial_sol = self._sol_from_assign(n_items, n_periods, trial)
                            if problem.is_feasible(trial_sol):
                                return trial_sol
                            # Mantener el cambio si al menos no rompe la estructura y aporta cobertura.
                            y = trial
                            candidate = trial_sol
                            improved = True
                            break
                    if improved:
                        break
                if not improved:
                    break

        return candidate


def build_component(problem, randomness: float = 0.25, late_bias: float = 0.4):
    return CapacityBalancedBlockConstructor(randomness=randomness, late_bias=late_bias)
