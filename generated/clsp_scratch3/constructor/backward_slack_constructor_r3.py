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
    """Constructor hacia atrás: coloca setups antes de la demanda y evita asignaciones tardías."""

    def __init__(self, window: int = 4, risk: float = 0.35):
        self.window = window
        self.risk = risk

    def _empty(self, inst):
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int):
        if sol[i][t]:
            return sol
        row = list(sol[i])
        row[t] = True
        return sol[:i] + (tuple(row),) + sol[i + 1 :]

    def _first_positive_demand(self, inst, i: int):
        for t in range(inst.n_periods):
            if inst.demand[i][t] > 0:
                return t
        return None

    def _item_has_setup_prefix(self, sol, i: int, t: int) -> bool:
        return any(sol[i][tt] for tt in range(t + 1))

    def build(self, inst, rng: Random):
        sol = self._empty(inst)

        # 1) Anchor each item at or before its first positive demand.
        items = list(range(inst.n_items))
        items.sort(key=lambda i: (self._first_positive_demand(inst, i) is None, self._first_positive_demand(inst, i) or inst.n_periods, i))

        for i in items:
            first_d = self._first_positive_demand(inst, i)
            if first_d is None:
                continue
            # Prefer the first positive-demand period; if already occupied by the item, keep it.
            sol = self._set(sol, i, first_d)

        # 2) Backward coverage repair:
        # For any positive-demand period not yet preceded by a setup, add a setup exactly there.
        # This keeps the same basic backward idea but guarantees no demand appears before its first setup.
        for i in items:
            for t in range(inst.n_periods):
                if inst.demand[i][t] > 0 and not self._item_has_setup_prefix(sol, i, t):
                    sol = self._set(sol, i, t)

        # 3) If an item has demand but still no setup due to corner cases, place one at period 0.
        for i in items:
            if any(inst.demand[i][t] > 0 for t in range(inst.n_periods)) and not any(sol[i]):
                sol = self._set(sol, i, 0)

        return sol


def build_component(problem, window: int = 4, risk: float = 0.35):
    return BackwardSlackConstructor(window=window, risk=risk)
