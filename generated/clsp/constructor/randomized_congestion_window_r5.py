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
    """Constructor conservador con sesgo aleatorio hacia períodos tempranos
    con holgura, pero manteniendo una única ventana de setup por ítem para
    evitar patrones de cobertura innecesariamente fragmentados.
    """

    def __init__(self, alpha: float = 0.3, window: int = 4) -> None:
        self.alpha = alpha
        self.window = window

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        n, T = inst.n_items, inst.n_periods
        y = [[False for _ in range(T)] for _ in range(n)]

        remaining_setup_cap = [float(inst.capacity[t]) for t in range(T)]

        items = list(range(n))
        items.sort(
            key=lambda i: (
                min((t for t in range(T) if inst.demand[i][t] > 0), default=T),
                -sum(inst.demand[i][t] for t in range(T)),
                -inst.setup_time[i],
            )
        )

        # Pequeña perturbación reproducible que no altera la regla de cobertura.
        for k in range(len(items) - 1, 0, -1):
            if rng.random() <= self.alpha:
                j = rng.randint(0, k)
                items[k], items[j] = items[j], items[k]

        for i in items:
            demand_periods = [t for t in range(T) if inst.demand[i][t] > 0]
            if not demand_periods:
                continue

            first_dem = demand_periods[0]

            # Elegimos el setup lo más tarde posible antes de la primera demanda,
            # siempre respetando la capacidad del período.
            candidates = [
                t
                for t in range(0, first_dem + 1)
                if inst.setup_time[i] <= remaining_setup_cap[t]
            ]

            if candidates:
                # Preferimos períodos tardíos para reducir inventario; la aleatoriedad
                # solo desempata dentro de la ventana factible.
                candidates.sort(
                    key=lambda t: (
                        remaining_setup_cap[t],
                        -t,
                    ),
                    reverse=True,
                )
                top_k = min(len(candidates), max(1, int(round(self.alpha * len(candidates)))))
                chosen_t = candidates[rng.randint(0, top_k - 1)]
            else:
                # Fallback conservador: forzamos la primera demanda para no dejarla
                # sin cobertura. Esto solo ocurre si la guía por capacidad no encuentra
                # hueco suficiente.
                chosen_t = first_dem

            y[i][chosen_t] = True
            if remaining_setup_cap[chosen_t] >= float(inst.setup_time[i]):
                remaining_setup_cap[chosen_t] -= float(inst.setup_time[i])

        return tuple(tuple(row) for row in y)


def build_component(problem: Any, alpha: float = 0.3, window: int = 4):
    return RandomizedCongestionWindow(alpha=float(alpha), window=int(window))
