from __future__ import annotations

from random import Random


COMPONENT = {
    "name": "setup_merge_split_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "merge_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class SetupMergeSplitKick:
    def __init__(self, problem, merge_bias: float = 0.5):
        self.problem = problem
        self.merge_bias = merge_bias

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.problem.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        s = [list(row) for row in sol]

        # Candidate operations:
        # - merge: on an item with two consecutive setups, remove the later one
        # - split: on an item with a setup and a gap, duplicate/move to a neighboring period
        merge_candidates = []
        split_candidates = []
        for i in range(n_items):
            for t in range(n_periods - 1):
                if s[i][t] and s[i][t + 1]:
                    merge_candidates.append((i, t, t + 1))
                if s[i][t] and not s[i][t + 1]:
                    split_candidates.append((i, t, t + 1))
                if s[i][t] and t > 0 and not s[i][t - 1]:
                    split_candidates.append((i, t, t - 1))

        do_merge = bool(merge_candidates) and (not split_candidates or rng.random() < self.merge_bias)

        if do_merge:
            i, t1, t2 = rng.choice(merge_candidates)
            # Remove one of the consecutive setups, keeping the other.
            if rng.random() < 0.5:
                s[i][t1] = False
            else:
                s[i][t2] = False
        elif split_candidates:
            i, t_from, t_to = rng.choice(split_candidates)
            # Add a nearby setup to create a denser pattern.
            s[i][t_to] = True
            # Optionally deactivate the original to actually move the setup.
            if rng.random() < min(0.9, 0.25 * strength):
                s[i][t_from] = False
        else:
            # Fallback: flip a small structured block on one item.
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s[i][t] = not s[i][t]
            if n_periods > 1:
                tt = min(n_periods - 1, max(0, t + (1 if t == 0 else -1)))
                if tt != t:
                    s[i][tt] = not s[i][tt]

        new_sol = tuple(tuple(row) for row in s)
        if new_sol == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s[i][t] = not s[i][t]
            new_sol = tuple(tuple(row) for row in s)
        return new_sol


def build_component(problem, **params):
    return SetupMergeSplitKick(problem, merge_bias=float(params.get("merge_bias", 0.5)))
