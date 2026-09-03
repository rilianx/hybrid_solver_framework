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
    """Constructor por bloques: coloca un setup por ítem en un período permitido, balanceando capacidad."""

    def __init__(self, randomness: float = 0.25, late_bias: float = 0.4):
        self.randomness = randomness
        self.late_bias = late_bias

    def _sol_from_assign(self, n_items: int, n_periods: int, assign: List[int]) -> Tuple[Tuple[bool, ...], ...]:
        sol = [[False] * n_periods for _ in range(n_items)]
        for i, t in enumerate(assign):
            sol[i][t] = True
        return tuple(tuple(row) for row in sol)

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods

        first_demand = []
        for i in range(n_items):
            fd = next((t for t in range(n_periods) if inst.demand[i][t] > 0), n_periods - 1)
            first_demand.append(fd)

        # Orden: primero ítems más "pesados" y con menor flexibilidad.
        item_order = list(range(n_items))
        item_order.sort(
            key=lambda i: (
                first_demand[i],
                -(sum(inst.demand[i]) + 1.0) / max(inst.setup_cost[i], 1.0),
                -inst.setup_time[i],
                i,
            )
        )

        # Capacidad reservada para setups por período.
        remaining = [float(inst.capacity[t]) for t in range(n_periods)]
        assign = [-1] * n_items

        # Relleno inicial: período más tardío posible antes de la primera demanda, con sesgo a balancear capacidad.
        for i in item_order:
            eligible = list(range(first_demand[i] + 1))
            if not eligible:
                eligible = [0]

            scored = []
            for t in eligible:
                slack = remaining[t] - float(inst.setup_time[i])
                scored.append((slack, -t, t))
            # Preferimos el período con más holgura; late_bias desplaza hacia períodos más tardíos.
            scored.sort(reverse=True)
            if self.late_bias > 0.0 and len(scored) > 1:
                k = max(1, int((1.0 - self.late_bias) * len(scored)))
                scored = scored[:k] + scored[k:]
            chosen = None
            for _, _, t in scored:
                if remaining[t] >= inst.setup_time[i]:
                    chosen = t
                    break
            if chosen is None:
                # Fallback: el mejor período permitido aunque quede sobrecargado; luego se reparará con is_feasible.
                chosen = max(eligible, key=lambda t: (remaining[t], -t))
            assign[i] = chosen
            remaining[chosen] -= float(inst.setup_time[i])

        candidate = self._sol_from_assign(n_items, n_periods, assign)
        if hasattr(inst, "problem"):
            problem = inst.problem
            if problem.is_feasible(candidate):
                return candidate

            # Reparación elemental: mover un solo setup a otro período permitido si mejora factibilidad.
            for _ in range(n_items * n_periods):
                if problem.is_feasible(candidate):
                    return candidate
                best = None
                best_sol = None
                for i in range(n_items):
                    cur = assign[i]
                    for t in range(first_demand[i] + 1):
                        if t == cur:
                            continue
                        trial_assign = assign[:]
                        trial_assign[i] = t
                        trial = self._sol_from_assign(n_items, n_periods, trial_assign)
                        if problem.is_feasible(trial):
                            return trial
                        # Si no es factible, guardamos el cambio más "natural": más capacidad residual.
                        score = (remaining[t] - inst.setup_time[i], -t)
                        if best is None or score > best:
                            best = score
                            best_sol = trial_assign
                if best_sol is None:
                    break
                assign = best_sol
                candidate = self._sol_from_assign(n_items, n_periods, assign)

        return candidate


def build_component(problem, randomness: float = 0.25, late_bias: float = 0.4):
    return CapacityBalancedBlockConstructor(randomness=randomness, late_bias=late_bias)
