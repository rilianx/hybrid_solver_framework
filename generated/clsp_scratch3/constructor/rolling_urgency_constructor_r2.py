from __future__ import annotations

from random import Random

COMPONENT = {
    "name": "rolling_urgency_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "lookahead": {"type": "int", "range": [1, 8]},
        "slack_bias": {"type": "float", "range": [0.0, 2.0]},
    },
}


class RollingUrgencyConstructor:
    """Constructor secuencial: abre setups cuando la demanda futura acumulada supera la holgura esperada."""

    def __init__(self, lookahead: int = 3, slack_bias: float = 0.8):
        self.lookahead = lookahead
        self.slack_bias = slack_bias

    def _empty(self, inst):
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int):
        row = list(sol[i])
        row[t] = True
        return sol[:i] + (tuple(row),) + sol[i + 1 :]

    def _interval_need(self, inst, i: int, t: int) -> float:
        end = min(inst.n_periods, t + self.lookahead)
        return sum(inst.demand[i][tt] for tt in range(t, end))

    def build(self, inst, rng: Random):
        sol = self._empty(inst)

        # Precompute urgency information.
        total_demand = [sum(inst.demand[i][t] for t in range(inst.n_periods)) for i in range(inst.n_items)]
        item_order = sorted(
            range(inst.n_items),
            key=lambda i: (
                inst.holding_cost[i] / (1.0 + inst.setup_cost[i]),
                -total_demand[i],
                i,
            ),
        )

        # For each period, open setups for items that need coverage now or soon,
        # respecting the setup capacity of the period.
        for t in range(inst.n_periods):
            cap = inst.capacity[t]
            used = 0.0

            candidates = []
            for i in item_order:
                # If the item has any demand from t onward, it may need a setup by now.
                if sum(inst.demand[i][tt] for tt in range(t, inst.n_periods)) <= 0:
                    continue
                if sol[i][t]:
                    continue

                imminent = self._interval_need(inst, i, t)
                score = (imminent / (1.0 + inst.setup_time[i])) + self.slack_bias * inst.holding_cost[i]
                candidates.append((score, inst.setup_time[i], rng.random(), i))

            candidates.sort(reverse=True)

            # Greedily pack setups into the current period.
            for _, stime, _, i in candidates:
                if used + stime <= cap:
                    sol = self._set(sol, i, t)
                    used += stime

            # If the period is still very light, add a few proactive setups for near-future demand.
            if used < 0.4 * cap:
                extras = []
                for i in item_order:
                    if sol[i][t]:
                        continue
                    future_need = self._interval_need(inst, i, t + 1)
                    if future_need > 0:
                        extras.append((future_need, -inst.setup_time[i], rng.random(), i))
                extras.sort(reverse=True)

                for _, neg_stime, _, i in extras:
                    stime = -neg_stime
                    if used + stime <= cap * 0.85:
                        sol = self._set(sol, i, t)
                        used += stime

        return sol


def build_component(problem, lookahead: int = 3, slack_bias: float = 0.8):
    return RollingUrgencyConstructor(lookahead=lookahead, slack_bias=slack_bias)
