from random import Random

from examples.lotsizing.problem_model import Solution  # type: ignore

COMPONENT = {
    "name": "item_window_compaction",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class ItemWindowCompaction:
    def __init__(self, problem):
        self.problem = problem

    @staticmethod
    def _copy(sol):
        return [list(row) for row in sol]

    def perturb(self, sol: Solution, strength: float, rng: Random) -> Solution:
        inst = self.problem.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        k = max(1, int(round(strength)))

        y = self._copy(sol)

        for _ in range(k):
            i = rng.randrange(n_items)
            active = [t for t in range(n_periods) if y[i][t]]
            if len(active) <= 1:
                # Force a nontrivial change by inserting a setup in a free period.
                free = [t for t in range(n_periods) if not y[i][t]]
                if free:
                    t = free[rng.randrange(len(free))]
                    y[i][t] = True
                continue

            left = rng.choice(active)
            right = rng.choice(active)
            if left > right:
                left, right = right, left

            # Compact the item's setups to the endpoints of a random window.
            for t in range(left + 1, right):
                y[i][t] = False

            # Ensure the move is not a no-op.
            if left == right:
                choices = [t for t in range(n_periods) if t != left]
                if choices:
                    y[i][choices[rng.randrange(len(choices))]] = True

        return tuple(tuple(row) for row in y)


def build_component(problem, strength: float = 2.0):
    return ItemWindowCompaction(problem)
