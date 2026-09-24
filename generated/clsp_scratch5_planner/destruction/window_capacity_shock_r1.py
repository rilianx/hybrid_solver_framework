from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "window_capacity_shock",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "center_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class WindowCapacityShockDestruction:
    """
    Libera todos los setups dentro de una ventana contigua de períodos.

    La ventana se centra preferentemente en períodos con mayor "presión" de capacidad:
    - mayor demanda agregada relativa a la capacidad;
    - mayor carga de setups en esos períodos;
    - mayor desbalance acumulado demanda-capacidad (proxy de inventario/adelanto requerido).
    """

    def __init__(self, problem, inst, center_bias: float = 0.7):
        self.problem = problem
        self.inst = inst
        self.center_bias = center_bias

    def _period_scores(self, sol) -> list[float]:
        inst = self.inst
        n_periods = inst.n_periods
        n_items = inst.n_items

        demand_by_t = [sum(inst.demand[i][t] for i in range(n_items)) for t in range(n_periods)]
        setup_time_by_t = [
            sum(inst.setup_time[i] for i in range(n_items) if sol[i][t]) for t in range(n_periods)
        ]
        setup_count_by_t = [sum(1 for i in range(n_items) if sol[i][t]) for t in range(n_periods)]

        scores: list[float] = []
        cum_d = 0.0
        cum_cap = 0.0
        for t in range(n_periods):
            cum_d += demand_by_t[t]
            cum_cap += inst.capacity[t]
            imbalance = max(0.0, cum_d - cum_cap)

            cap = max(inst.capacity[t], 1e-9)
            local_pressure = (demand_by_t[t] + setup_time_by_t[t]) / cap
            setup_density = setup_count_by_t[t] / max(1, n_items)

            # Score alto cuando hay saturación local o necesidad de adelantar inventario.
            score = 1.5 * local_pressure + 0.8 * setup_density + 0.02 * imbalance
            scores.append(score)
        return scores

    def _choose_center(self, scores: list[float], rng: Random) -> int:
        n = len(scores)
        if n == 1:
            return 0

        best = max(scores)
        if best <= 0:
            return rng.randrange(n)

        # Mezcla entre explotación y muestreo sesgado por score.
        if rng.random() < self.center_bias:
            top = sorted(range(n), key=lambda t: scores[t], reverse=True)
            top_k = top[: max(1, min(3, n))]
            return rng.choice(top_k)

        weights = [max(0.0, s) + 1e-9 for s in scores]
        total = sum(weights)
        r = rng.random() * total
        acc = 0.0
        for t, w in enumerate(weights):
            acc += w
            if acc >= r:
                return t
        return n - 1

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_periods = self.inst.n_periods
        n_items = self.inst.n_items

        # Ventana contigua en períodos.
        window_len = max(1, int(round(ratio * n_periods)))
        window_len = min(window_len, n_periods)

        scores = self._period_scores(sol)
        center = self._choose_center(scores, rng)

        left = window_len // 2
        start = center - left
        end = start + window_len
        if start < 0:
            end -= start
            start = 0
        if end > n_periods:
            start -= end - n_periods
            end = n_periods
        start = max(0, start)
        end = min(n_periods, end)

        # Asegura ventana no vacía.
        if start >= end:
            start = max(0, min(center, n_periods - 1))
            end = min(n_periods, start + 1)

        free_vars = {var_name(i, t) for t in range(start, end) for i in range(n_items)}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2, center_bias: float = 0.7):
    return WindowCapacityShockDestruction(problem, problem.inst, center_bias=center_bias)
