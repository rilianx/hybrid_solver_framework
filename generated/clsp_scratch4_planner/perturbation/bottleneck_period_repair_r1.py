from __future__ import annotations

from math import ceil
from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, Solution, var_name  # type: ignore

COMPONENT = {
    "name": "bottleneck_period_repair",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class BottleneckPeriodRepair:
    """Kick heurístico guiado por congestión de períodos."""

    def __init__(self, problem: Any, default_strength: float = 2.0):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.default_strength = default_strength

    def _period_loads(self, sol: Solution) -> list[float]:
        inst = self.inst
        loads = []
        for t in range(inst.n_periods):
            setup_time = sum(inst.setup_time[i] for i in range(inst.n_items) if sol[i][t])
            # Congestión relativa: tiempo de setup respecto a capacidad.
            loads.append(setup_time / max(inst.capacity[t], 1e-9))
        return loads

    def _sorted_bottlenecks(self, sol: Solution) -> list[int]:
        loads = self._period_loads(sol)
        return sorted(range(self.inst.n_periods), key=lambda t: (loads[t], t), reverse=True)

    def perturb(self, sol: Solution, strength: float, rng: Random) -> Solution:
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        strength = max(1.0, float(strength))
        loads = self._period_loads(sol)
        bottlenecks = sorted(range(n_periods), key=lambda t: (loads[t], t), reverse=True)

        # Número de setups a "destruir": más fuerte => más agresivo.
        target_moves = max(1, min(n_items * n_periods, int(ceil(strength))))
        new_sol = [list(row) for row in sol]

        # Trabajamos primero en los períodos más saturados.
        moved = 0
        bottleneck_pool = bottlenecks[: max(1, min(n_periods, int(ceil(strength / 2.0))))]
        for t in bottleneck_pool:
            active_items = [i for i in range(n_items) if new_sol[i][t]]
            if not active_items:
                continue

            # Destruye setups en este período priorizando ítems de mayor tiempo de setup.
            rng.shuffle(active_items)
            active_items.sort(key=lambda i: inst.setup_time[i], reverse=True)

            for i in active_items:
                if moved >= target_moves:
                    break

                # Busca vecino menos cargado: t-1 o t+1.
                candidates = []
                if t - 1 >= 0:
                    candidates.append(t - 1)
                if t + 1 < n_periods:
                    candidates.append(t + 1)

                if candidates:
                    # Preferir el vecino con menor carga y, a igualdad, menor capacidad usada por setups.
                    best = min(
                        candidates,
                        key=lambda tt: (loads[tt], sum(inst.setup_time[k] for k in range(n_items) if new_sol[k][tt]), tt),
                    )
                    # Mover setup: apagar en t y encender en el vecino.
                    if best != t:
                        new_sol[i][t] = False
                        new_sol[i][best] = True
                        moved += 1
                        # Actualiza cargas aproximadas.
                        loads[t] = max(0.0, loads[t] - inst.setup_time[i] / max(inst.capacity[t], 1e-9))
                        loads[best] = loads[best] + inst.setup_time[i] / max(inst.capacity[best], 1e-9)
                else:
                    # En bordes: eliminar temporalmente para que el LP reequilibre.
                    if new_sol[i][t]:
                        new_sol[i][t] = False
                        moved += 1
                        loads[t] = max(0.0, loads[t] - inst.setup_time[i] / max(inst.capacity[t], 1e-9))

                if moved >= target_moves:
                    break

        # Garantiza que la solución cambie para strength >= 1.
        if tuple(tuple(row) for row in new_sol) == sol:
            # Fallback: toma el setup más pesado en el período más congestionado y muévelo al vecino menos cargado.
            for t in bottlenecks:
                active_items = [i for i in range(n_items) if sol[i][t]]
                if not active_items:
                    continue
                i = max(active_items, key=lambda ii: inst.setup_time[ii])
                candidates = [tt for tt in (t - 1, t + 1) if 0 <= tt < n_periods]
                if candidates:
                    best = min(candidates, key=lambda tt: loads[tt])
                    new_sol = [list(row) for row in sol]
                    new_sol[i][t] = False
                    new_sol[i][best] = True
                    break
                else:
                    new_sol = [list(row) for row in sol]
                    new_sol[i][t] = False
                    break

        return tuple(tuple(row) for row in new_sol)


def build_component(problem, **params):
    strength = float(params.get("strength", 2.0))
    return BottleneckPeriodRepair(problem, default_strength=strength)
