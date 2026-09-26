from __future__ import annotations

from math import inf
from typing import Iterable


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
    """Puntúa acciones de construcción con una idea diferente a la extensión más cercana:
    sesga el tour hacia clientes periféricos y hacia cierres de ruta que evitan dejar
    demasiado espacio residual, usando además una noción de "futuro" basada en la
    distancia al conjunto restante.
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
            r = int(r)
            if r == c:
                continue
            d = self._dist(c, r)
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

            last = int(open_route[-1])
            depot_pull = self._dist(last, 0)

            if remaining_list:
                # Close routes when the tail is near the depot and the route is already
                # sufficiently packed; this differs from "nearest extension" by focusing
                # on route termination quality rather than immediate insertion proximity.
                frontier = self._nearest_remaining_distance(last, remaining_list)
                return self.close_weight * (
                    0.55 * (depot_pull / max(depot_pull + frontier, 1e-9))
                    + 0.45 * (slack / max(cap, 1e-9))
                )

            return self.close_weight * (depot_pull / max(cap, 1e-9))

        c = int(action[1])
        demand = self._demand(c)
        nearest_future = self._nearest_remaining_distance(c, remaining_list)
        depot = self._dist(0, c)

        if not open_route:
            # Start with a peripheral client that is also useful as a bridge to the
            # remaining pool: this intentionally pushes the construction away from
            # nearest-neighbor behavior.
            load_ratio = demand / max(cap, 1e-9)
            balance = abs(load_ratio - 0.5)
            return (
                self.radius_weight * (0.75 * depot - 0.25 * nearest_future)
                + self.balance_weight * balance
            )

        last = int(open_route[-1])
        load_before = sum(self._demand(x) for x in open_route)
        load_after = load_before + demand
        slack_after = max(0.0, cap - load_after)

        attach_cost = self._dist(last, c)

        # Prefer candidates that are not merely close to the current tail, but that
        # also lie on the periphery and maintain a useful "future" bridge.
        load_ratio = load_after / max(cap, 1e-9)
        balance = abs(load_ratio - 0.65)

        return (
            self.radius_weight * (0.65 * attach_cost + 0.35 * depot - 0.25 * nearest_future)
            + self.balance_weight * (balance + 0.5 * slack_after / max(cap, 1e-9))
        )


def build_component(problem, radius_weight: float = 1.0, balance_weight: float = 1.0, close_weight: float = 5.0):
    return LookaheadBalanceAndRadius(
        problem,
        radius_weight=radius_weight,
        balance_weight=balance_weight,
        close_weight=close_weight,
    )
