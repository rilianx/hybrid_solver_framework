from random import Random

from generated.clsp_setups_cycle.model.parts import canonical

COMPONENT = {
    "name": "adjacent_setup_shift",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "merge_prob": {"type": "float", "range": [0.0, 1.0]},
        "max_attempts_factor": {"type": "int", "range": [2, 20]},
    },
}


class AdjacentSetupShift:
    def __init__(self, problem, merge_prob: float = 0.3, max_attempts_factor: int = 8):
        self.problem = problem
        self.merge_prob = float(merge_prob)
        self.max_attempts_factor = int(max_attempts_factor)

    def perturb(self, sol, strength: float, rng: Random):
        base = canonical(sol)
        n = len(base)
        if n == 0 or len(base[0]) == 0:
            return base
        T = len(base[0])
        s = [list(row) for row in base]
        k = max(1, int(round(strength)))
        moves = 0
        attempts = 0
        max_attempts = self.max_attempts_factor * k + 10
        while moves < k and attempts < max_attempts:
            attempts += 1
            i = rng.randrange(n)
            on = [t for t in range(T) if s[i][t]]
            if not on or T < 2:
                continue
            t = rng.choice(on)
            dirs = [d for d in (-1, 1) if 0 <= t + d < T]
            d = rng.choice(dirs)
            u = t + d
            if not s[i][u]:
                s[i][t] = False
                s[i][u] = True
                moves += 1
            elif rng.random() < self.merge_prob:
                s[i][t] = False
                moves += 1
        new = canonical(s)
        if new == base:
            i = rng.randrange(n)
            t = rng.randrange(T)
            s = [list(row) for row in base]
            s[i][t] = not s[i][t]
            new = canonical(s)
        return new


def build_component(problem, merge_prob: float = 0.3, max_attempts_factor: int = 8):
    return AdjacentSetupShift(problem, merge_prob=merge_prob, max_attempts_factor=max_attempts_factor)
