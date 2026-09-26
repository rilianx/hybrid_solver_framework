from __future__ import annotations

from math import inf
from typing import Any, Iterable, Sequence


COMPONENT = {
    "name": "lookahead_balance_and_radius",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "radius_weight": {"type": "float", "range": [0.0, 10.0]},
        "balance_weight": {"type": "float", "range": [0.0, 10.0]},
        "close_weight": {"type": "float", "range": [0.0, 1000.0]},
    },
}


class LookaheadBalanceAndRadius:
    """Puntúa acciones de construcción con una idea distinta:
    prioriza anclar el tour en clientes que sean buenos "puentes" hacia el resto
    de clientes no asignados, usando el vecindario del candidato en el conjunto
    restante, además de una penalización suave por desbalance de carga.
    Menor puntaje = mejor."""

    def __init__(
        self,
        problem,
        radius_weight: float = 1.0,
        balance_weight: float = 1.0,
        close_weight: float = 5.0,
    ):
        self.inst = problem.inst
        self.radius_weight = float(radius_weight)
        self.balance_weight = float(balance_weight)
        self.close_weight = float(close_weight)

    def _dist(self, i: int, j: int) -> float:
        return float(self.inst.dist(i, j))

    def _demand(self, c: int) -> float:
        return float(self.inst.demand[c])

    def _nearest_remaining_distance(self, c: int, remaining: Iterable[int]) -> float:
        best = inf
        for r in remaining:
            if r == c:
                continue
            d = self._dist(c, int(r))
            if d < best:
                best = d
        return 0.0 if best is inf else best

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]
        cap = float(self.inst.capacity)

        remaining_list = list(remaining) if remaining is not None else []

        if kind == "close":
            if not open_route:
                return 0.0
            load = sum(self._demand(c) for c in open_route)
            slack = max(0.0, cap - load)

            if remaining_list:
                last = int(open_route[-1])
                bridge = self._nearest_remaining_distance(last, remaining_list)
                depot_pull = self._dist(last, 0)
                # Close when the current tail is poorly connected to what remains,
                # and when the route is already reasonably packed.
                return self.close_weight * (
                    0.6 * (slack / max(cap, 1e-9)) + 0.4 * (bridge / max(depot_pull + bridge, 1e-9))
                )
            return 0.0

        c = int(action[1])
        demand = self._demand(c)

        if not open_route:
            # Start a route with a client that sits in a dense region of the unassigned set.
            nearest_future = self._nearest_remaining_distance(c, remaining_list)
            depot = self._dist(0, c)
            load_ratio = demand / max(cap, 1e-9)
            balance = abs(load_ratio - 0.5)
            return self.radius_weight * (0.5 * depot + 0.5 * nearest_future) + self.balance_weight * balance

        last = int(open_route[-1])
        load_before = sum(self._demand(x) for x in open_route)
        load_after = load_before + demand
        slack_after = max(0.0, cap - load_after)

        # Use a bridge criterion over the remaining unassigned clients rather than
        # only the immediate tail-to-candidate extension.
        bridge_cost = self._nearest_remaining_distance(c, remaining_list)
        attach_cost = self._dist(last, c)

        # Mild load balancing: prefer not to pack too early nor leave too much slack.
        load_ratio = load_after / max(cap, 1e-9)
        balance = abs(load_ratio - 0.65)

        return (
            self.radius_weight * (0.7 * attach_cost + 0.3 * bridge_cost)
            + self.balance_weight * (balance + slack_after / max(cap, 1e-9))
        )


def build_component(problem, radius_weight: float = 1.0, balance_weight: float = 1.0, close_weight: float = 5.0):
    return LookaheadBalanceAndRadius(
        problem,
        radius_weight=radius_weight,
        balance_weight=balance_weight,
        close_weight=close_weight,
    )
