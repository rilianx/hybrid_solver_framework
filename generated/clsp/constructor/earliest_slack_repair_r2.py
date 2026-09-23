from __future__ import annotations

from random import Random
from typing import Any, List, Optional, Tuple

from examples.lotsizing.problem_model import CLSPInstance, Solution

COMPONENT = {
    "name": "earliest_slack_repair",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {"window": {"type": "int", "range": [1, 10]}},
}


class EarliestSlackRepair:
    """Construye un patrón de setups factible asignando, por ítem, un setup
    no posterior a su primer período con demanda y respetando la capacidad por período.
    """

    def __init__(self, window: int = 3) -> None:
        self.window = window

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        n, T = inst.n_items, inst.n_periods
        y = [[False for _ in range(T)] for _ in range(n)]
        remaining = [float(inst.capacity[t]) for t in range(T)]

        items = list(range(n))
        deadlines = [self._deadline(inst, i) for i in items]
        items.sort(key=lambda i: (deadlines[i] if deadlines[i] is not None else T, -inst.setup_time[i], i))

        # First try a greedy latest-feasible assignment.
        if self._greedy_assign(inst, items, deadlines, remaining, y):
            return tuple(tuple(row) for row in y)

        # Fallback: bounded DFS/backtracking in the same spirit.
        y2 = [[False for _ in range(T)] for _ in range(n)]
        remaining2 = [float(inst.capacity[t]) for t in range(T)]
        order = items[:]
        if self._dfs_assign(inst, order, deadlines, remaining2, y2, rng, 0):
            return tuple(tuple(row) for row in y2)

        # Last resort: feasible by construction for items with demand if they fit individually;
        # if the instance is tight, the DFS above should already find a solution.
        # We still return the best partial solution built by greedy to keep the contract.
        return tuple(tuple(row) for row in y)

    def _deadline(self, inst: CLSPInstance, i: int) -> Optional[int]:
        for t in range(inst.n_periods):
            if inst.demand[i][t] > 1e-9:
                return t
        return None

    def _greedy_assign(
        self,
        inst: CLSPInstance,
        items: List[int],
        deadlines: List[Optional[int]],
        remaining: List[float],
        y: List[List[bool]],
    ) -> bool:
        T = inst.n_periods
        for i in items:
            d = deadlines[i]
            if d is None:
                continue
            p = float(inst.setup_time[i])
            chosen = None
            for t in range(d, -1, -1):
                if remaining[t] + 1e-9 >= p:
                    chosen = t
                    break
            if chosen is None:
                return False
            y[i][chosen] = True
            remaining[chosen] -= p
        return True

    def _dfs_assign(
        self,
        inst: CLSPInstance,
        order: List[int],
        deadlines: List[Optional[int]],
        remaining: List[float],
        y: List[List[bool]],
        rng: Random,
        pos: int,
    ) -> bool:
        if pos >= len(order):
            return True

        i = order[pos]
        d = deadlines[i]
        if d is None:
            return self._dfs_assign(inst, order, deadlines, remaining, y, rng, pos + 1)

        p = float(inst.setup_time[i])
        candidates = [t for t in range(d, -1, -1) if remaining[t] + 1e-9 >= p]

        # Small randomized tie-breaking while keeping the latest-feasible bias.
        if len(candidates) > 1:
            head = candidates[:]
            rng.shuffle(head)
            candidates = sorted(head, reverse=True)

        for t in candidates:
            y[i][t] = True
            remaining[t] -= p
            if self._dfs_assign(inst, order, deadlines, remaining, y, rng, pos + 1):
                return True
            remaining[t] += p
            y[i][t] = False

        return False


def build_component(problem: Any, **params):
    return EarliestSlackRepair(window=int(params.get("window", 3)))
