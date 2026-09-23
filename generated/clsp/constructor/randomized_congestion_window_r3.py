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
    con holgura, para permitir adelantar producción y evitar saturaciones
    puntuales en períodos de demanda.
    """

    def __init__(self, alpha: float = 0.3, window: int = 4) -> None:
        self.alpha = alpha
        self.window = window

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        n, T = inst.n_items, inst.n_periods
        y = [[False for _ in range(T)] for _ in range(n)]

        # Carga base por período: demanda total (proxy de congestión).
        period_load = [0.0 for _ in range(T)]
        for t in range(T):
            period_load[t] = sum(inst.demand[i][t] for i in range(n))

        # Capacidad "libre" aproximada tras setups; usamos solo como guía.
        remaining_setup_cap = [float(inst.capacity[t]) for t in range(T)]

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
            demand_periods = [t for t in range(T) if inst.demand[i][t] > 0]
            if not demand_periods:
                continue

            first_dem = demand_periods[0]
            last_dem = demand_periods[-1]

            # Candidatos: períodos no posteriores a la primera demanda, priorizando
            # aquellos con más holgura y menor congestión.
            candidates = []
            for t in range(0, first_dem + 1):
                if inst.setup_time[i] <= remaining_setup_cap[t]:
                    score = (
                        remaining_setup_cap[t],
                        -period_load[t],
                        -t,
                    )
                    candidates.append((score, t))

            if candidates:
                candidates.sort(reverse=True)
                # Sesgo aleatorio controlado: elegimos entre los mejores candidatos.
                top_k = min(len(candidates), max(1, int(round(self.alpha * len(candidates)))))
                chosen_idx = rng.randint(0, top_k - 1)
                chosen_t = candidates[chosen_idx][1]
            else:
                # Si no hay holgura suficiente en períodos tempranos, usamos el
                # primer período con demanda para garantizar cobertura.
                chosen_t = first_dem

            y[i][chosen_t] = True
            remaining_setup_cap[chosen_t] -= float(inst.setup_time[i])

            # Refuerzo conservador: para ítems con demanda dispersa, añadimos algunos
            # setups extra en períodos de demanda para aumentar flexibilidad, pero
            # sin forzar todos los períodos.
            for t in demand_periods[1:]:
                if rng.random() <= self.alpha and inst.setup_time[i] <= remaining_setup_cap[t]:
                    y[i][t] = True
                    remaining_setup_cap[t] -= float(inst.setup_time[i])

            # Si el ítem tiene demanda muy dispersa y la ventana lo sugiere, abrimos
            # algún setup adicional dentro de una ventana temprana para facilitar
            # adelantos de producción.
            if self.window > 1 and last_dem > first_dem:
                t_end = min(T - 1, first_dem + self.window - 1)
                window_candidates = [
                    t for t in range(first_dem + 1, t_end + 1)
                    if not y[i][t] and inst.setup_time[i] <= remaining_setup_cap[t]
                ]
                if window_candidates and rng.random() <= self.alpha:
                    t_extra = window_candidates[rng.randint(0, len(window_candidates) - 1)]
                    y[i][t_extra] = True
                    remaining_setup_cap[t_extra] -= float(inst.setup_time[i])

        return tuple(tuple(row) for row in y)


def build_component(problem: Any, alpha: float = 0.3, window: int = 4):
    return RandomizedCongestionWindow(alpha=float(alpha), window=int(window))
