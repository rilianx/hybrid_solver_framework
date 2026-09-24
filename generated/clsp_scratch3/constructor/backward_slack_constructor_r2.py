from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "backward_slack_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "window": {"type": "int", "range": [1, 10]},
        "risk": {"type": "float", "range": [0.0, 1.0]},
    },
}


class BackwardSlackConstructor:
    """Constructor hacia atrás: coloca setups en períodos con mayor holgura y empuja la producción a esos puntos."""

    def __init__(self, window: int = 4, risk: float = 0.35):
        self.window = window
        self.risk = risk

    def _empty(self, inst):
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int):
        row = list(sol[i])
        row[t] = True
        return sol[:i] + (tuple(row),) + sol[i + 1 :]

    def _prefix_demand(self, inst, i: int, t: int) -> float:
        return sum(inst.demand[i][tt] for tt in range(t + 1))

    def _score_period(self, inst, t: int) -> float:
        demand = sum(inst.demand[i][t] for i in range(inst.n_items))
        return inst.capacity[t] - demand - 0.5 * sum(inst.setup_time)

    def _setup_load(self, inst, sol, t: int) -> float:
        return sum(inst.setup_time[i] for i in range(inst.n_items) if sol[i][t])

    def _within_setup_capacity(self, inst, sol) -> bool:
        return all(self._setup_load(inst, sol, t) <= inst.capacity[t] for t in range(inst.n_periods))

    def build(self, inst, rng: Random):
        sol = self._empty(inst)

        period_order = sorted(range(inst.n_periods), key=lambda t: (self._score_period(inst, t), -t), reverse=True)
        item_order = sorted(
            range(inst.n_items),
            key=lambda i: (
                -inst.setup_cost[i] / (1.0 + inst.holding_cost[i]),
                -sum(inst.demand[i]),
                inst.setup_time[i],
            ),
        )

        # Pass 1: assign one anchor setup to each item near the best slack period before its main demand mass.
        for i in item_order:
            demand_by_t = [inst.demand[i][t] for t in range(inst.n_periods)]
            if sum(demand_by_t) <= 0:
                continue
            main_t = max(range(inst.n_periods), key=lambda t: (demand_by_t[t], -t))
            candidates = [t for t in period_order if t <= main_t]
            if not candidates:
                candidates = [0]
            chosen_t = max(candidates, key=lambda t: (self._score_period(inst, t), -abs(main_t - t), rng.random()))
            sol = self._set(sol, i, chosen_t)

        # Pass 2: add extra setups backward where an item's prefix demand is large compared with its local coverage.
        for i in item_order:
            active = [t for t in range(inst.n_periods) if sol[i][t]]
            active.sort()
            if not active:
                sol = self._set(sol, i, 0)
                active = [0]
            for t in range(inst.n_periods - 1, -1, -1):
                if inst.demand[i][t] <= 0:
                    continue
                covered = any(tt <= t for tt in active)
                if not covered:
                    best_prev = max((tt for tt in range(t + 1)), key=lambda tt: (self._score_period(inst, tt), -tt, rng.random()))
                    sol = self._set(sol, i, best_prev)
                    active.append(best_prev)
                    active.sort()

        # Repair by adding setups in the most capacious periods if needed.
        for _ in range(inst.n_items * inst.n_periods * 4):
            if self._within_setup_capacity(inst, sol):
                break
            slack = [(inst.capacity[t] - self._setup_load(inst, sol, t), t) for t in range(inst.n_periods)]
            slack.sort(reverse=True)
            best_t = slack[0][1]
            best_i = None
            best_score = None
            for i in range(inst.n_items):
                if sol[i][best_t]:
                    continue
                score = self._prefix_demand(inst, i, best_t) / (1.0 + inst.setup_time[i] + self.risk * inst.holding_cost[i])
                if best_score is None or score > best_score or (score == best_score and rng.random() < 0.5):
                    best_score = score
                    best_i = i
            if best_i is None:
                break
            sol = self._set(sol, best_i, best_t)

        if not self._within_setup_capacity(inst, sol):
            # Conservative fallback: spread one setup per item across the most slack periods.
            # Keep the same basic idea, but avoid relying on external problem state.
            for i in range(inst.n_items):
                if any(sol[i]):
                    continue
                best_t = max(range(inst.n_periods), key=lambda t: (inst.capacity[t] - self._setup_load(inst, sol, t), -t, rng.random()))
                sol = self._set(sol, i, best_t)

        return sol


def build_component(problem, window: int = 4, risk: float = 0.35):
    return BackwardSlackConstructor(window=window, risk=risk)
