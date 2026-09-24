from random import Random

from examples.lotsizing.problem_model import Solution  # type: ignore

COMPONENT = {
    "name": "adjacent_setup_relocation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class AdjacentSetupRelocation:
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
            true_pos = [(i, t) for i in range(n_items) for t in range(n_periods) if y[i][t]]
            if not true_pos:
                break
            i, t = true_pos[rng.randrange(len(true_pos))]
            candidates = []
            if t > 0:
                candidates.append(t - 1)
            if t + 1 < n_periods:
                candidates.append(t + 1)
            if not candidates:
                continue
            nt = candidates[rng.randrange(len(candidates))]
            if nt == t:
                continue
            y[i][t] = False
            y[i][nt] = True

        return tuple(tuple(row) for row in y)


def build_component(problem, strength: float = 2.0):
    return AdjacentSetupRelocation(problem)
