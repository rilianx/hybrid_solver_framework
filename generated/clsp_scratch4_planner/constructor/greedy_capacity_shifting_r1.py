from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, var_name


COMPONENT = {
    "name": "greedy_capacity_shifting",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "lookahead": {"type": "int", "range": [1, 12]},
        "shift_window": {"type": "int", "range": [0, 12]},
        "cost_bias": {"type": "float", "range": [0.0, 5.0]},
        "random_tie_break": {"type": "bool", "range": [0, 1]},
    },
}


@dataclass
class GreedyCapacityShiftingConstructor:
    """Constructor voraz: recorre períodos e reparte carga hacia atrás cuando hay holgura.

    La estrategia intenta mantener capacidad futura suficiente:
    - activa setups solo cuando una demanda futura no puede seguir cubriéndose
      con la capacidad remanente;
    - si un período se congestiona, adelanta producción a períodos anteriores
      con holgura;
    - prioriza ítems con mayor demanda acumulada y menor costo de inventario.
    """

    lookahead: int = 6
    shift_window: int = 6
    cost_bias: float = 1.0
    random_tie_break: bool = False

    def _build_one(self, inst: CLSPInstance, rng: Random) -> tuple[tuple[bool, ...], ...]:
        n, T = inst.n_items, inst.n_periods
        demand = inst.demand
        cap = list(inst.capacity)

        # Setup pattern we will construct.
        y = [[False for _ in range(T)] for _ in range(n)]

        # Remaining demand by item and period suffix.
        suffix = [[0.0 for _ in range(T + 1)] for _ in range(n)]
        for i in range(n):
            acc = 0.0
            for t in range(T - 1, -1, -1):
                acc += demand[i][t]
                suffix[i][t] = acc

        # Residual capacity per period after accounting for chosen setups.
        residual = cap[:]

        # Prioritize cheap-holding / urgent items.
        def item_score(i: int, t: int) -> tuple[float, float, float, int]:
            rem = suffix[i][t]
            urgency = rem / max(1.0, float(T - t))
            h = inst.holding_cost[i]
            s = inst.setup_cost[i]
            # Lower holding cost and higher urgency first; setup cost slightly biases
            # toward items whose early production is less "expensive" to carry.
            score = urgency / max(1e-9, h) + self.cost_bias * (1.0 / max(1.0, s))
            if self.random_tie_break:
                return (-score, h, s, rng.randint(0, 10**9))
            return (-score, h, s, i)

        # Forward sweep by period, packing items into residual capacity.
        produced = [0.0 for _ in range(n)]
        for t in range(T):
            # Demand that must already be covered by end of period t.
            due = [(i, suffix[i][t]) for i in range(n) if suffix[i][t] > produced[i] + 1e-9]
            due.sort(key=lambda it: item_score(it[0], t))

            # Greedily reserve capacity for items with the most urgent remaining demand.
            while True:
                chosen = None
                best_take = 0.0
                best_key: Any = None

                for i, rem in due:
                    need = rem - produced[i]
                    if need <= 1e-9:
                        continue
                    if not y[i][t]:
                        avail = residual[t] - inst.setup_time[i]
                    else:
                        avail = residual[t]
                    if avail <= 1e-9:
                        continue
                    take = min(need, avail)
                    if take <= 1e-9:
                        continue
                    key = item_score(i, t)
                    # Prefer items with larger urgency, then lower holding cost.
                    if chosen is None or key < best_key or (key == best_key and take > best_take):
                        chosen = i
                        best_take = take
                        best_key = key

                if chosen is None:
                    break

                i = chosen
                if not y[i][t]:
                    y[i][t] = True
                    residual[t] -= inst.setup_time[i]
                # Produce as much as possible for this item now.
                take = min(suffix[i][t] - produced[i], residual[t])
                if take <= 1e-9:
                    break
                produced[i] += take
                residual[t] -= take

            # If period is still congested by its own setups, we can try to shift
            # some items backwards into earlier slack periods.
            if residual[t] < -1e-9:
                # Repair by moving some active setups from t to earlier periods with slack.
                overloaded = -residual[t]
                active = [i for i in range(n) if y[i][t]]
                active.sort(key=lambda i: (inst.holding_cost[i], inst.setup_cost[i], -suffix[i][t]))
                for i in active:
                    if overloaded <= 1e-9:
                        break
                    # Find earlier period with enough slack to host this setup.
                    moved = False
                    for p in range(max(0, t - self.shift_window), t):
                        if residual[p] >= inst.setup_time[i] + 1e-9:
                            y[i][p] = True
                            residual[p] -= inst.setup_time[i]
                            # Keep t setup as well if needed; if not, removing it may help.
                            if residual[t] + inst.setup_time[i] <= cap[t] + 1e-9:
                                y[i][t] = False
                                residual[t] += inst.setup_time[i]
                                overloaded = max(0.0, -residual[t])
                            moved = True
                            break
                    if not moved:
                        continue

        sol = tuple(tuple(row) for row in y)

        # Light deterministic repair: if infeasible, add setups for missing items
        # in the earliest period that still has slack.
        # This is conservative and keeps determinism.
        if hasattr(self, "_problem") and not self._problem.is_feasible(sol):
            # Try a few rounds of adding earlier setups for items that have demand.
            yy = [list(r) for r in sol]
            for _ in range(T * n):
                if self._problem.is_feasible(tuple(tuple(r) for r in yy)):
                    break
                improved = False
                for i in range(n):
                    for t in range(T):
                        if suffix[i][t] <= 1e-9:
                            continue
                        if yy[i][t]:
                            continue
                        # Add a setup in an earlier period with some slack.
                        for p in range(t, -1, -1):
                            yy[i][p] = True
                            trial = tuple(tuple(r) for r in yy)
                            if self._problem.is_feasible(trial):
                                improved = True
                                break
                            yy[i][p] = False
                        if improved:
                            break
                    if improved:
                        break
                if not improved:
                    break
            sol = tuple(tuple(r) for r in yy)

        return sol

    def build(self, inst: CLSPInstance, rng: Random):
        # The problem is injected by build_component; stored only for repair checks.
        return self._build_one(inst, rng)


def build_component(problem, lookahead: int = 6, shift_window: int = 6, cost_bias: float = 1.0, random_tie_break: bool = False):
    comp = GreedyCapacityShiftingConstructor(
        lookahead=lookahead,
        shift_window=shift_window,
        cost_bias=cost_bias,
        random_tie_break=random_tie_break,
    )
    comp._problem = problem
    return comp
