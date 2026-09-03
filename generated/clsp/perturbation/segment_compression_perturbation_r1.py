from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import LotSizingModel, CLSPInstance


COMPONENT = {
    "name": "segment_compression_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "items_to_reseed": {"type": "int", "range": [1, 3]},
        "preserve_first_setup": {"type": "bool", "range": [0, 1]},
    },
}


class SegmentCompressionPerturbation:
    def __init__(self, problem: LotSizingModel, items_to_reseed: int = 1, preserve_first_setup: bool = True):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.items_to_reseed = items_to_reseed
        self.preserve_first_setup = preserve_first_setup

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        k = max(1, min(self.items_to_reseed, int(round(strength))))
        chosen_items = rng.sample(range(n_items), min(k, n_items))
        new = [list(row) for row in sol]

        for i in chosen_items:
            row = list(sol[i])
            if not any(row):
                # If the row is empty, seed one setup in a demand-positive period.
                candidates = [t for t in range(n_periods) if inst.demand[i][t] > 0.0]
                t = rng.choice(candidates) if candidates else rng.randrange(n_periods)
                row[t] = True
                new[i] = row
                continue

            # Compress consecutive setup segments: keep at most one setup per run
            # and optionally preserve the first setup of the original row.
            compressed = [False] * n_periods
            t = 0
            while t < n_periods:
                if row[t]:
                    run_end = t
                    while run_end + 1 < n_periods and row[run_end + 1]:
                        run_end += 1
                    if self.preserve_first_setup:
                        compressed[t] = True
                    else:
                        compressed[run_end] = True
                    t = run_end + 1
                else:
                    t += 1

            # If compression did not change anything, perturb by moving one setup
            # to the nearest gap to create a structurally different pattern.
            if tuple(compressed) == sol[i]:
                ones = [t for t, v in enumerate(row) if v]
                t0 = rng.choice(ones)
                compressed[t0] = False
                if t0 + 1 < n_periods:
                    compressed[t0 + 1] = True
                else:
                    compressed[max(0, t0 - 1)] = True

            new[i] = compressed

        candidate = tuple(tuple(r) for r in new)
        if candidate == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            new = [list(row) for row in sol]
            new[i][t] = not new[i][t]
            candidate = tuple(tuple(r) for r in new)
        return candidate


def build_component(problem, **params):
    return SegmentCompressionPerturbation(
        problem,
        items_to_reseed=int(params.get("items_to_reseed", 1)),
        preserve_first_setup=bool(params.get("preserve_first_setup", True)),
    )
