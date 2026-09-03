from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "neighbor_shift_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "radius": {"type": "int", "range": [1, 3]},
    },
}


class NeighborShiftPerturbation:
    def __init__(self, problem: Any, radius: int = 1):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.radius = max(1, int(radius))

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        s = [list(row) for row in sol]

        moves = max(1, int(round(strength)))
        for _ in range(moves):
            i = rng.randrange(n_items)
            true პერიოდs = [t for t in range(n_periods) if s[i][t]]
            if not true_periods:
                t0 = rng.randrange(n_periods)
                s[i][t0] = True
                continue

            t0 = rng.choice(true_periods)
            direction = rng.choice([-1, 1])
            step = rng.randint(1, self.radius)
            t1 = t0 + direction * step
            if t1 < 0 or t1 >= n_periods:
                candidates = [t for t in range(n_periods) if not s[i][t]]
                if candidates:
                    t1 = rng.choice(candidates)
                else:
                    t1 = t0

            if t1 != t0:
                s[i][t0] = False
                s[i][t1] = True
            else:
                # guaranteed change if we could not relocate
                flip = rng.randrange(n_periods)
                s[i][flip] = not s[i][flip]

        out = tuple(tuple(row) for row in s)
        if out == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s = [list(row) for row in sol]
            s[i][t] = not s[i][t]
            out = tuple(tuple(row) for row in s)
        return out


def build_component(problem, **params):
    radius = params.get("radius", 1)
    return NeighborShiftPerturbation(problem, radius=radius)
