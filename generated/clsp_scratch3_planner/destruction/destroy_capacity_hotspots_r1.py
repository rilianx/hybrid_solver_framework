from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "destroy_capacity_hotspots",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "hotspot_bias": {"type": "float", "range": [0.5, 2.5]},
    },
}


class DestroyCapacityHotspots:
    """Libera setups en períodos temporalmente congestionados, priorizando los de mayor tiempo de setup."""

    def __init__(self, problem, inst, hotspot_bias: float = 1.5):
        self.problem = problem
        self.inst = inst
        self.hotspot_bias = hotspot_bias

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        # Congestión temporal: carga de setup relativa a la capacidad en cada período.
        period_info = []
        for t in range(n_periods):
            active_items = [i for i in range(n_items) if sol[i][t]]
            setup_load = sum(self.inst.setup_time[i] for i in active_items)
            cap = self.inst.capacity[t]
            saturation = setup_load / cap if cap > 0 else float("inf")
            # Fuerte sesgo hacia períodos más saturados; desempate por cantidad de setups.
            score = saturation * self.hotspot_bias + len(active_items) / max(1, n_items)
            period_info.append((score, saturation, len(active_items), t, active_items))

        period_info.sort(reverse=True)

        free_vars: set[str] = set()
        selected_periods = []
        # Selecciona uno o varios hotspots hasta acumular suficiente destrucción.
        for score, saturation, n_active, t, active_items in period_info:
            if not active_items:
                continue
            selected_periods.append((t, active_items, saturation))
            if len(free_vars) >= k:
                break
            # Si el período está poco cargado, aún puede entrar si es de los más altos.
            if len(selected_periods) >= 1 and (saturation >= 0.75 or len(selected_periods) == 1):
                pass

        # Si no hubo setups en los hotspots iniciales, usar cualquier período con setups.
        if not selected_periods:
            for _, _, _, t, active_items in period_info:
                if active_items:
                    selected_periods.append((t, active_items, 0.0))
                    break

        # Libera primero los setups de mayor tiempo dentro de los períodos más congestionados.
        for t, active_items, saturation in selected_periods:
            active_items_sorted = sorted(
                active_items,
                key=lambda i: (
                    self.inst.setup_time[i],
                    self.inst.setup_cost[i],
                    rng.random(),
                ),
                reverse=True,
            )

            # Cuántos setups liberar en este hotspot:
            # - más agresivo si el período está muy saturado
            # - al menos uno por período seleccionado
            remaining = k - len(free_vars)
            if remaining <= 0:
                break
            if saturation >= 0.95:
                quota = max(1, min(remaining, len(active_items_sorted)))
            elif saturation >= 0.80:
                quota = max(1, min(remaining, max(1, (len(active_items_sorted) + 1) // 2)))
            else:
                quota = max(1, min(remaining, 1 + len(active_items_sorted) // 3))

            for i in active_items_sorted:
                free_vars.add(var_name(i, t))
                if len(free_vars) >= k or quota <= 1:
                    quota -= 1
                    if len(free_vars) >= k:
                        break
                else:
                    quota -= 1

            if len(free_vars) >= k:
                break

        # Si aún faltan variables libres, completar con más setups en los períodos más cargados.
        if len(free_vars) < k:
            for _, _, _, t, active_items in period_info:
                for i in sorted(active_items, key=lambda i: (self.inst.setup_time[i], self.inst.setup_cost[i]), reverse=True):
                    v = var_name(i, t)
                    if v not in free_vars:
                        free_vars.add(v)
                        if len(free_vars) >= k:
                            break
                if len(free_vars) >= k:
                    break

        # Garantía de al menos una variable liberada.
        if not free_vars:
            for t in range(n_periods):
                for i in range(n_items):
                    if sol[i][t]:
                        free_vars.add(var_name(i, t))
                        break
                if free_vars:
                    break
            if not free_vars:
                free_vars.add(var_name(0, 0))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, hotspot_bias: float = 1.5):
    return DestroyCapacityHotspots(problem, problem.inst, hotspot_bias=hotspot_bias)
