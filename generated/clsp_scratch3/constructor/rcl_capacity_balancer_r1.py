from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "rcl_capacity_balancer",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "alpha": {"type": "float", "range": [0.05, 1.0]},
        "temperature": {"type": "float", "range": [0.1, 5.0]},
    },
}


class CapacityBalancedRCLConstructor:
    """GRASP constructivo: lista restringida aleatoria sobre ítems urgentes y períodos con más capacidad libre."""

    def __init__(self, alpha: float = 0.3, temperature: float = 1.2):
        self.alpha = alpha
        self.temperature = temperature

    def _empty(self, inst):
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int):
        row = list(sol[i])
        row[t] = True
        return sol[:i] + (tuple(row),) + sol[i + 1 :]

    def _future_pressure(self, inst, i: int, t: int) -> float:
        end = min(inst.n_periods, t + 3)
        return sum((end - tt) * inst.demand[i][tt] for tt in range(t, end))

    def build(self, inst, rng: Random):
        sol = self._empty(inst)
        period_load = [0.0] * inst.n_periods

        item_order = list(range(inst.n_items))
        rng.shuffle(item_order)
        item_order.sort(key=lambda i: (-sum(inst.demand[i]), inst.setup_time[i], inst.holding_cost[i]))

        # First pass: one or two setups per item in high-capacity periods.
        for i in item_order:
            total_d = sum(inst.demand[i])
            if total_d <= 0:
                continue
            candidates = list(range(inst.n_periods))
            candidates.sort(key=lambda t: (inst.capacity[t] - period_load[t], -t), reverse=True)
            rcl_size = max(1, int(len(candidates) * self.alpha))
            chosen = rng.choice(candidates[:rcl_size])
            sol = self._set(sol, i, chosen)
            period_load[chosen] += inst.setup_time[i]

            # second proactive setup if demand is spread out or setup cost is high
            if total_d > 0 and (inst.setup_cost[i] / (1.0 + inst.holding_cost[i]) > self.temperature * 50 or rng.random() < 0.35):
                future = [t for t in range(chosen + 1, inst.n_periods)]
                if future:
                    future.sort(key=lambda t: (inst.capacity[t] - period_load[t], self._future_pressure(inst, i, t), -t), reverse=True)
                    rcl_size2 = max(1, int(len(future) * self.alpha))
                    chosen2 = rng.choice(future[:rcl_size2])
                    if not sol[i][chosen2]:
                        sol = self._set(sol, i, chosen2)
                        period_load[chosen2] += inst.setup_time[i]

        # Repair: repeatedly open setups where they most reduce forecasted shortage.
        for _ in range(inst.n_items * inst.n_periods * 5):
            if problem.is_feasible(sol):
                break
            best = None
            best_score = None
            for t in range(inst.n_periods):
                free = inst.capacity[t] - period_load[t]
                for i in range(inst.n_items):
                    if sol[i][t]:
                        continue
                    urgency = self._future_pressure(inst, i, t)
                    score = (urgency + 1.0) * (free + 1.0) / (1.0 + inst.setup_time[i])
                    if best_score is None or score > best_score or (score == best_score and rng.random() < 0.5):
                        best_score = score
                        best = (i, t)
            if best is None:
                break
            i, t = best
            sol = self._set(sol, i, t)
            period_load[t] += inst.setup_time[i]

        # Final deterministic rescue: ensure every positive-demand item has at least one setup.
        for i in range(inst.n_items):
            if any(sol[i]):
                continue
            t = max(range(inst.n_periods), key=lambda tt: (inst.capacity[tt] - period_load[tt], -tt, rng.random()))
            sol = self._set(sol, i, t)
            period_load[t] += inst.setup_time[i]

        if not problem.is_feasible(sol):
            # last repair round with a stronger bias to early periods
            for _ in range(inst.n_items * inst.n_periods * 3):
                if problem.is_feasible(sol):
                    break
                t = max(range(inst.n_periods), key=lambda tt: (inst.capacity[tt] - period_load[tt], -tt))
                i = max(range(inst.n_items), key=lambda ii: (self._future_pressure(inst, ii, t), -inst.setup_time[ii]))
                if not sol[i][t]:
                    sol = self._set(sol, i, t)
                    period_load[t] += inst.setup_time[i]
                else:
                    break
        return sol


def build_component(problem, alpha: float = 0.3, temperature: float = 1.2):
    return CapacityBalancedRCLConstructor(alpha=alpha, temperature=temperature)
