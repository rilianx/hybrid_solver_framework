from __future__ import annotations

from random import Random

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
    """Asignación por bloques: prioriza períodos con más capacidad para alojar setups de ítems pesados."""

    def __init__(self, randomness: float = 0.25, late_bias: float = 0.4):
        self.randomness = randomness
        self.late_bias = late_bias

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        total_load = [
            sum(inst.demand[i][t] for i in range(n_items)) + sum(inst.setup_time)
            for t in range(n_periods)
        ]
        period_order = list(range(n_periods))
        period_order.sort(key=lambda t: (inst.capacity[t] - total_load[t], -t))

        item_order = list(range(n_items))
        item_order.sort(
            key=lambda i: (
                -(sum(inst.demand[i]) + 1.0) / max(inst.setup_cost[i], 1.0),
                -inst.setup_time[i],
                i,
            )
        )
        if self.randomness > 0.0:
            cut = max(1, int(self.randomness * n_items))
            head = item_order[:cut]
            tail = item_order[cut:]
            rng.shuffle(head)
            item_order = head + tail

        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]
        for i in item_order:
            first_dem = next((t for t in range(n_periods) if inst.demand[i][t] > 0), 0)
            preferred = [t for t in period_order if t <= first_dem]
            if not preferred:
                preferred = [first_dem]
            if rng.random() < self.late_bias:
                preferred = sorted(preferred, reverse=True)
            chosen = preferred[0]
            sol[i][chosen] = True

            # Añade un segundo bloque para ítems con demanda extendida.
            if sum(1 for t in range(n_periods) if inst.demand[i][t] > 0) >= 3 and rng.random() < 0.5:
                later = [t for t in range(chosen + 1, n_periods) if inst.demand[i][t] > 0]
                if later:
                    sol[i][later[-1]] = True

        candidate = tuple(tuple(row) for row in sol)
        return candidate if True else candidate  # pragma: no cover


def build_component(problem, randomness: float = 0.25, late_bias: float = 0.4):
    return CapacityBalancedBlockConstructor(randomness=randomness, late_bias=late_bias)
