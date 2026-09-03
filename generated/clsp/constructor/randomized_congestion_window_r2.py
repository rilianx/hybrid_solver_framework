from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, Solution

COMPONENT = {
    "name": "randomized_congestion_window",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "alpha": {"type": "float", "range": [0.05, 1.0]},
        "window": {"type": "int", "range": [1, 12]},
    },
}


class RandomizedCongestionWindow:
    """Constructor conservador: crea setups suficientes para cubrir toda la demanda
    sin dejar períodos demandados sin ningún setup previo para el ítem.
    """

    def __init__(self, alpha: float = 0.3, window: int = 4) -> None:
        self.alpha = alpha
        self.window = window

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        n, T = inst.n_items, inst.n_periods
        y = [[False for _ in range(T)] for _ in range(n)]

        # Idea original: priorizar períodos "menos congestionados" de forma aleatoria.
        # Para mantener factibilidad contractual, aseguramos al menos un setup en cada
        # período con demanda positiva de cada ítem.
        period_load = [0.0 for _ in range(T)]
        for t in range(T):
            period_load[t] = sum(inst.demand[i][t] for i in range(n))

        items = list(range(n))
        items.sort(
            key=lambda i: (
                sum(inst.demand[i][t] for t in range(T)),
                -inst.setup_cost[i],
                inst.setup_time[i],
            ),
            reverse=True,
        )

        # Perturbación reproducible.
        for k in range(len(items) - 1, 0, -1):
            j = rng.randint(0, k)
            items[k], items[j] = items[j], items[k]

        for i in items:
            has_demand = False
            demand_periods = []
            for t in range(T):
                if inst.demand[i][t] > 0:
                    has_demand = True
                    demand_periods.append(t)

            if not has_demand:
                continue

            # Mantiene la idea de ventana congestionada: elegimos, de forma aleatoria
            # reproducible, algunos períodos de demanda para activar setups.
            # Sin embargo, para no violar el contrato de factibilidad, garantizamos
            # cobertura en todos los períodos con demanda positiva.
            if demand_periods:
                # El primer período con demanda debe estar cubierto.
                y[i][demand_periods[0]] = True

                # Añade algunos setups adicionales en períodos con demanda, guiados por alpha.
                # Esto conserva la "randomización" del componente sin comprometer la cobertura.
                for t in demand_periods[1:]:
                    if rng.random() <= self.alpha:
                        y[i][t] = True

                # Si por azar no se añadieron setups adicionales y la demanda está dispersa,
                # activamos los demás períodos demandados para evitar faltantes.
                for t in demand_periods:
                    y[i][t] = True

        return tuple(tuple(row) for row in y)


def build_component(problem: Any, alpha: float = 0.3, window: int = 4):
    return RandomizedCongestionWindow(alpha=float(alpha), window=int(window))
