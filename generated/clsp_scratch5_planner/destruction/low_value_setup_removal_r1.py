from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "low_value_setup_removal",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "focus_bias": {"type": "float", "range": [0.0, 1.0]},
        "slack_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class LowValueSetupRemoval:
    """Libera setups con baja utilidad marginal estimada.

    La utilidad se aproxima a partir de:
    - coste de setup del ítem;
    - demanda futura cubierta por ese setup hasta el siguiente setup del mismo ítem;
    - carga de inventario inducida por producir antes de tiempo;
    - congestión del período, para evitar destruir setups claramente estratégicos.
    """

    def __init__(self, problem, focus_bias: float = 0.55, slack_bias: float = 0.25):
        self.problem = problem
        self.inst = problem.inst
        self.focus_bias = float(focus_bias)
        self.slack_bias = float(slack_bias)

    def _active_setups(self, sol):
        inst = self.inst
        active = []
        for i in range(inst.n_items):
            for t in range(inst.n_periods):
                if sol[i][t]:
                    active.append((i, t))
        return active

    def _period_loads(self, sol):
        inst = self.inst
        loads = []
        for t in range(inst.n_periods):
            prod_like = 0.0
            st = 0.0
            for i in range(inst.n_items):
                if sol[i][t]:
                    prod_like += inst.demand[i][t]
                    st += inst.setup_time[i]
            loads.append(prod_like + st)
        return loads

    def _next_setup_after(self, sol, i: int, t: int) -> int | None:
        for u in range(t + 1, self.inst.n_periods):
            if sol[i][u]:
                return u
        return None

    def _utility(self, sol, i: int, t: int, period_loads) -> float:
        inst = self.inst
        nxt = self._next_setup_after(sol, i, t)
        end = nxt if nxt is not None else inst.n_periods

        covered = 0.0
        inventory_burden = 0.0
        for u in range(t, end):
            d = inst.demand[i][u]
            covered += d
            inventory_burden += (u - t) * d * inst.holding_cost[i]

        span = max(1, end - t)
        avg_load = period_loads[t] / max(1, inst.capacity[t])
        slack = max(0.0, 1.0 - avg_load)

        # Alta utilidad si el setup cubre mucha demanda, evita mucho inventario
        # y está en un período apretado; baja utilidad si el lote es pequeño.
        setup_gain = inst.setup_cost[i] * (1.0 + 0.15 * self.focus_bias)
        demand_gain = covered * (0.25 + 0.75 * self.focus_bias)
        holding_penalty = inventory_burden * (0.10 + 0.40 * self.slack_bias)
        period_penalty = (1.0 - slack) * inst.setup_time[i] * (0.5 + 0.5 * self.slack_bias)

        return (setup_gain + demand_gain) / (1.0 + holding_penalty + period_penalty + 0.5 * span)

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        inst = self.inst
        all_vars = set(assignment.keys())

        active = self._active_setups(sol)
        if not active:
            # Devolver al menos una variable libre.
            chosen = {rng.choice(tuple(all_vars))}
            partial = {v: val for v, val in assignment.items() if v not in chosen}
            return partial, chosen

        period_loads = self._period_loads(sol)
        ranked = sorted(
            active,
            key=lambda it: (
                self._utility(sol, it[0], it[1], period_loads),
                rng.random(),
            ),
        )

        k = max(1, int(round(ratio * len(active))))
        k = min(k, len(active))

        chosen_setups = ranked[:k]
        free_vars = {var_name(i, t) for i, t in chosen_setups}

        # Garantizar que no liberamos todo por accidente si hay demasiada ratio.
        if not free_vars:
            i, t = ranked[0]
            free_vars.add(var_name(i, t))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    focus_bias = params.get("focus_bias", 0.55)
    slack_bias = params.get("slack_bias", 0.25)
    return LowValueSetupRemoval(problem, focus_bias=focus_bias, slack_bias=slack_bias)
