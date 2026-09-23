from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "saturation_balancing_shift",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "window": {"type": "int", "range": [1, 12]},
        "shift_prob": {"type": "float", "range": [0.0, 1.0]},
        "prefer_early": {"type": "bool", "range": [0, 1]},
    },
}


class SaturationBalancingShift:
    """Constructor que reparte setups desde períodos saturados hacia períodos vecinos con holgura."""

    def __init__(self, window: int = 4, shift_prob: float = 0.7, prefer_early: bool = True):
        self.window = window
        self.shift_prob = shift_prob
        self.prefer_early = prefer_early

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        demand_sum = [sum(inst.demand[i][t] for t in range(n_periods)) for i in range(n_items)]
        first_demand = []
        last_demand = []
        for i in range(n_items):
            fd = None
            ld = None
            for t in range(n_periods):
                if inst.demand[i][t] > 1e-12:
                    if fd is None:
                        fd = t
                    ld = t
            first_demand.append(fd)
            last_demand.append(ld)

        items = [i for i in range(n_items) if demand_sum[i] > 1e-12]
        items.sort(key=lambda i: (first_demand[i] if first_demand[i] is not None else n_periods, -demand_sum[i], i))

        remaining_periods = list(range(n_periods))
        remaining_periods.sort(key=lambda t: (t, -inst.capacity[t] if self.prefer_early else inst.capacity[t]))

        assigned_periods = {i: [] for i in range(n_items)}
        for t in remaining_periods:
            candidates = []
            for i in items:
                if last_demand[i] is not None and t > last_demand[i]:
                    continue
                score = (
                    0 if first_demand[i] is not None and t <= first_demand[i] else 1,
                    -(first_demand[i] if first_demand[i] is not None else n_periods),
                    -demand_sum[i],
                    i,
                )
                candidates.append((score, i))
            if not candidates:
                continue
            candidates.sort(key=lambda x: x[0])
            chosen = candidates[0][1]
            sol[chosen][t] = True
            assigned_periods[chosen].append(t)

        # Garantiza al menos un setup no posterior a la primera demanda para cada ítem con demanda.
        for i in items:
            if first_demand[i] is None:
                continue
            if any(sol[i][t] for t in range(0, first_demand[i] + 1)):
                continue
            sol[i][first_demand[i]] = True

        # Refuerza ítems cuya demanda total es grande respecto a la capacidad disponible antes de su último período.
        for i in items:
            if demand_sum[i] <= 1e-12:
                continue
            current_setups = [t for t in range(n_periods) if sol[i][t]]
            current_cap = sum(max(0.0, inst.capacity[t] - inst.setup_time[i]) for t in current_setups)
            if current_cap + 1e-9 >= demand_sum[i]:
                continue

            for t in range(n_periods):
                if sol[i][t]:
                    continue
                if first_demand[i] is not None and t > last_demand[i] and current_setups:
                    break
                sol[i][t] = True
                current_setups.append(t)
                current_cap += max(0.0, inst.capacity[t] - inst.setup_time[i])
                if current_cap + 1e-9 >= demand_sum[i]:
                    break

        # Corrimiento local de setups para mejorar la saturación, sin romper factibilidad por capacidad del período.
        loads = [sum(inst.setup_time[i] for i in range(n_items) if sol[i][t]) for t in range(n_periods)]
        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                if first_demand[i] is not None and t <= first_demand[i]:
                    continue
                if rng.random() > self.shift_prob:
                    continue

                candidates = []
                for dt in range(-self.window, self.window + 1):
                    if dt == 0:
                        continue
                    tt = t + dt
                    if tt < 0 or tt >= n_periods:
                        continue
                    if loads[tt] + inst.setup_time[i] <= inst.capacity[tt] + 1e-12:
                        candidates.append(tt)

                if not candidates:
                    continue
                candidates.sort(key=lambda tt: (loads[tt], tt if self.prefer_early else -tt))
                best_tt = candidates[0]
                if loads[best_tt] + inst.setup_time[i] < loads[t] - 1e-12:
                    sol[i][t] = False
                    sol[i][best_tt] = True
                    loads[t] -= inst.setup_time[i]
                    loads[best_tt] += inst.setup_time[i]

        return tuple(tuple(row) for row in sol)


def build_component(problem, window: int = 4, shift_prob: float = 0.7, prefer_early: bool = True):
    return SaturationBalancingShift(window=window, shift_prob=shift_prob, prefer_early=prefer_early)
