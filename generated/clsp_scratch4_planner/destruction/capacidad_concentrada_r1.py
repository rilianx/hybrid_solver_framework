from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "capacidad_concentrada",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
    },
}


class CapacidadConcentradaDestruction:
    """Libera setups concentrándose en los períodos con mayor saturación de capacidad.

    La saturación se aproxima con la carga de tiempos de setup sobre la capacidad
    del período, y se libera una fracción de las variables de esos períodos para
    forzar redistribución temporal.
    """

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst
        self._groups = problem.variable_groups(inst)

        self._period_vars: list[list[str]] = []
        for t in range(inst.n_periods):
            self._period_vars.append(self._groups.get(f"t{t}", []))

        self._var_to_period: dict[str, int] = {}
        for t, vars_t in enumerate(self._period_vars):
            for v in vars_t:
                self._var_to_period[v] = t

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)

        inst = self.inst
        period_loads: list[tuple[float, int]] = []
        for t in range(inst.n_periods):
            load = 0.0
            for i in range(inst.n_items):
                if sol[i][t]:
                    load += inst.setup_time[i]
            cap = inst.capacity[t]
            saturation = load / cap if cap > 1e-12 else load
            period_loads.append((saturation, t))

        period_loads.sort(key=lambda x: (x[0], x[1]), reverse=True)

        total_vars = len(assignment)
        target_free = max(1, int(round(ratio * total_vars)))

        selected_periods: list[int] = []
        free_vars: set[str] = set()

        # Prioriza períodos más saturados y libera una fracción de sus setups.
        for sat, t in period_loads:
            if len(free_vars) >= target_free:
                break

            vars_t = [v for v in self._period_vars[t] if v in assignment]
            active_t = [v for v in vars_t if assignment[v] >= 0.5]

            # Si el período está vacío, también puede liberarse un pequeño subconjunto
            # de variables para dar oportunidad a reubicar producción hacia allí.
            pool = active_t if active_t else vars_t
            if not pool:
                continue

            selected_periods.append(t)
            remaining = target_free - len(free_vars)

            # Más saturación => liberamos más dentro del período, pero sin exceder lo pedido.
            frac = 0.35 + 0.45 * min(1.0, max(0.0, sat))
            k = max(1, min(len(pool), int(round(frac * len(pool)))))
            k = min(k, remaining)

            chosen = rng.sample(pool, k) if k < len(pool) else list(pool)
            free_vars.update(chosen)

        # Garantía: si todavía no alcanzamos el objetivo, completamos con setups
        # de los períodos más saturados.
        if len(free_vars) < target_free:
            for _, t in period_loads:
                if len(free_vars) >= target_free:
                    break
                vars_t = [v for v in self._period_vars[t] if v in assignment and v not in free_vars]
                active_t = [v for v in vars_t if assignment[v] >= 0.5]
                pool = active_t if active_t else vars_t
                if not pool:
                    continue
                needed = target_free - len(free_vars)
                chosen = rng.sample(pool, min(len(pool), needed))
                free_vars.update(chosen)

        # Último recurso: si por alguna razón no hay variables activas, liberar alguna variable cualquiera.
        if not free_vars:
            all_vars = list(assignment.keys())
            free_vars.add(rng.choice(all_vars))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25):
    return CapacidadConcentradaDestruction(problem, problem.inst)
