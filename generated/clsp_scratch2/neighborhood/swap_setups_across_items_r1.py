from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import ProblemModel

COMPONENT = {
    "name": "swap_setups_across_items",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "period_focus": {"type": "cat", "values": ["all", "dense", "sparse"]},
        "min_gap": {"type": "float", "range": [0.0, 1000.0]},
    },
}


class SwapSetupsAcrossItemsNeighborhood:
    """Intercambia un setup entre dos ítems en el mismo período."""

    def __init__(self, problem: ProblemModel, period_focus: str = "all", min_gap: float = 0.0):
        self.problem = problem
        self.inst = problem.inst
        self.period_focus = period_focus
        self.min_gap = min_gap

    def _periods(self):
        inst = self.inst
        if self.period_focus == "all":
            return range(inst.n_periods)
        loads = []
        for t in range(inst.n_periods):
            load = sum(inst.demand[i][t] + inst.setup_time[i] for i in range(inst.n_items) if True)
            loads.append((load / inst.capacity[t], t))
        loads.sort()
        if self.period_focus == "dense":
            return [t for _, t in loads[len(loads) // 2 :]]
        return [t for _, t in loads[: max(1, len(loads) // 2)]]

    def moves(self, sol) -> Iterable[tuple[int, int, int]]:
        inst = self.inst
        periods = set(self._periods())
        for t in periods:
            active = [i for i in range(inst.n_items) if sol[i][t]]
            inactive = [i for i in range(inst.n_items) if not sol[i][t]]
            for i in active:
                for j in inactive:
                    # filtro suave para evitar demasiados swaps triviales
                    if abs(inst.setup_cost[i] - inst.setup_cost[j]) < self.min_gap:
                        yield (i, j, t)

    def apply(self, sol, m):
        i, j, t = m
        s = [list(row) for row in sol]
        s[i][t] = False
        s[j][t] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, j, t = m
        return self.apply(sol, (j, i, t))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, period_focus: str = "all", min_gap: float = 0.0):
    return SwapSetupsAcrossItemsNeighborhood(problem, period_focus=period_focus, min_gap=min_gap)
