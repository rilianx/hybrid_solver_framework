from __future__ import annotations

from typing import Iterable
import random

from examples.lotsizing.problem_model import Solution, CLSPInstance, LotSizingModel


COMPONENT = {
    "name": "item_block_toggle",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "block_length": {"type": "int", "range": [1, 4]},
        "mode": {"type": "cat", "values": ["prefix", "suffix", "window"]},
    },
}


class ItemBlockToggle:
    """Activa o desactiva un bloque contiguo de setups de un mismo ítem.
    Movimiento = (i, start, length, value).
    """

    def __init__(self, problem: LotSizingModel, block_length: int = 2, mode: str = "window"):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.block_length = block_length
        self.mode = mode

    def moves(self, sol: Solution) -> Iterable[tuple[int, int, int, bool]]:
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        L = min(self.block_length, n_periods)
        for i in range(n_items):
            if self.mode == "prefix":
                starts = [0]
            elif self.mode == "suffix":
                starts = [max(0, n_periods - L)]
            else:
                starts = range(0, n_periods - L + 1)
            for start in starts:
                current = all(sol[i][t] for t in range(start, start + L))
                yield (i, start, L, not current)
                yield (i, start, L, current)

    def apply(self, sol: Solution, m: tuple[int, int, int, bool]) -> Solution:
        i, start, length, value = m
        return tuple(
            tuple(
                (value if i2 == i and start <= t < start + length else sol[i2][t])
                for t in range(self.inst.n_periods)
            )
            for i2 in range(self.inst.n_items)
        )

    def undo(self, sol: Solution, m: tuple[int, int, int, bool]) -> Solution:
        i, start, length, value = m
        return tuple(
            tuple(
                ((not value) if i2 == i and start <= t < start + length else sol[i2][t])
                for t in range(self.inst.n_periods)
            )
            for i2 in range(self.inst.n_items)
        )

    def delta(self, sol: Solution, m: tuple[int, int, int, bool]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, block_length: int = 2, mode: str = "window"):
    return ItemBlockToggle(problem, block_length=block_length, mode=mode)
