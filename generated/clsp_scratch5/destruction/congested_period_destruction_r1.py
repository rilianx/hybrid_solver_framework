from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "congested_period_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "window_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class CongestedPeriodDestruction:
    """Libera setups en los períodos más cargados; destruye una franja temporal con sesgo a congestión."""

    def __init__(self, problem, inst, window_bias: float = 0.35):
        self.problem = problem
        self.inst = inst
        self.window_bias = window_bias

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        all_vars = [var_name(i, t) for t in range(n_periods) for i in range(n_items)]

        k = max(1, int(round(ratio * len(all_vars))))
        # Carga por período: setups activos ponderados por tiempo de setup, más un pequeño sesgo aleatorio.
        loads = []
        for t in range(n_periods):
            load = 0.0
            for i in range(n_items):
                if sol[i][t]:
                    load += self.inst.setup_time[i] + 0.1 * self.inst.setup_cost[i]
            load += self.window_bias * rng.random()
            loads.append((load, t))
        loads.sort(reverse=True)

        # Elegimos una ventana contigua centrada alrededor del período más cargado.
        center = loads[0][1]
        half = max(0, int(round((k / max(1, n_items)) / 2)))
        start = max(0, center - half)
        end = min(n_periods - 1, center + half)
        chosen = {var_name(i, t) for t in range(start, end + 1) for i in range(n_items) if sol[i][t]}

        # Si aún faltan variables por liberar, completamos con los períodos más cargados.
        for _, t in loads:
            if len(chosen) >= k:
                break
            for i in range(n_items):
                if sol[i][t]:
                    chosen.add(var_name(i, t))
                    if len(chosen) >= k:
                        break

        # Garantía de al menos una variable libre.
        if not chosen:
            t = center
            i = rng.randrange(n_items)
            chosen.add(var_name(i, t))

        # Ajuste final exacto si nos pasamos.
        if len(chosen) > k:
            chosen = set(rng.sample(sorted(chosen), k))

        free_vars = chosen
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2, window_bias: float = 0.35):
    return CongestedPeriodDestruction(problem, problem.inst, window_bias=window_bias)
