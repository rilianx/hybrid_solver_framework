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
    """Constructor por bloques: activa setups de forma conservadora para cubrir la demanda."""

    def __init__(self, randomness: float = 0.25, late_bias: float = 0.4):
        self.randomness = randomness
        self.late_bias = late_bias

    def _sol_from_assign(self, assign: List[List[bool]]) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(tuple(row) for row in assign)

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods

        y = [[False] * n_periods for _ in range(n_items)]

        first_demand = []
        total_demand = []
        demand_periods_by_item = []
        for i in range(n_items):
            periods = [t for t in range(n_periods) if inst.demand[i][t] > 0]
            demand_periods_by_item.append(periods)
            first_demand.append(periods[0] if periods else n_periods)
            total_demand.append(sum(inst.demand[i]))

        # Ítems más urgentes primero: demanda temprana y mayor carga.
        item_order = list(range(n_items))
        item_order.sort(
            key=lambda i: (
                first_demand[i],
                -(total_demand[i] + 1.0) / max(float(inst.setup_cost[i]), 1.0),
                -float(inst.setup_time[i]),
                i,
            )
        )

        # Reparación/constructivo conservador:
        # Procesamos los períodos de izquierda a derecha y activamos setups de ítems
        # que ya tienen demanda pendiente, priorizando aquellos cuya primera demanda es más temprana.
        remaining = [sum(inst.demand[i]) for i in range(n_items)]
        assigned = [False] * n_items

        for t in range(n_periods):
            # Ítems que pueden necesitar producirse a más tardar en este período.
            candidates = [
                i for i in item_order
                if remaining[i] > 0 and first_demand[i] <= t
            ]

            if not candidates:
                continue

            # Capacidad reservada con una cota simple: un setup por período suele ser suficiente
            # para evitar sobrecargar la capacidad y, a la vez, cubrir la demanda a tiempo.
            # Si el período queda holgado, intentamos añadir un segundo ítem solo si es muy barato.
            chosen: List[int] = []

            # Primero, el más urgente.
            chosen.append(candidates[0])

            # Ocasionalmente añadimos otro ítem si la aleatoriedad lo permite y la presión temporal es baja.
            if len(candidates) > 1 and self.randomness > 0.0 and rng.random() < self.randomness:
                second = candidates[1]
                if (
                    first_demand[second] == first_demand[chosen[0]]
                    and rng.random() < self.late_bias
                ):
                    chosen.append(second)

            for i in chosen:
                y[i][t] = True
                assigned[i] = True
                # Consumimos una parte conservadora de la demanda pendiente.
                # No alteramos la solución final: esto solo guía la selección de setups.
                if remaining[i] > 0:
                    remaining[i] = max(0, remaining[i] - max(1, int(inst.capacity[t] // max(1.0, float(inst.setup_time[i]) + 1.0))))

        # Aseguramos al menos un setup por ítem con demanda.
        # Si un ítem todavía no recibió setup y tiene demanda, lo colocamos en su primer período de demanda.
        for i in item_order:
            if total_demand[i] <= 0:
                continue
            if not assigned[i]:
                t = first_demand[i]
                if t >= n_periods:
                    t = n_periods - 1
                y[i][t] = True

            # Refuerzo leve: si hay demanda en varios períodos y la primera demanda es temprana,
            # activamos también el último período con demanda para evitar huecos de cobertura.
            if demand_periods_by_item[i]:
                t_last = demand_periods_by_item[i][-1]
                if t_last != first_demand[i] and self.randomness > 0.0 and rng.random() < self.randomness * 0.5:
                    y[i][t_last] = True

        candidate = self._sol_from_assign(y)
        return candidate


def build_component(problem, randomness: float = 0.25, late_bias: float = 0.4):
    return CapacityBalancedBlockConstructor(randomness=randomness, late_bias=late_bias)
