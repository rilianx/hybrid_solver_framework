from random import Random

from generated.clsp_setups_cycle.model.parts import canonical

COMPONENT = {
    "name": "period_window_reshuffle",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "open_prob": {"type": "float", "range": [0.2, 0.9]},
        "keep_prob": {"type": "float", "range": [0.0, 0.8]},
    },
}


class PeriodWindowReshuffle:
    def __init__(self, problem, open_prob: float = 0.6, keep_prob: float = 0.3):
        self.problem = problem
        self.open_prob = float(open_prob)
        self.keep_prob = float(keep_prob)

    def perturb(self, sol, strength: float, rng: Random):
        base = canonical(sol)
        n = len(base)
        if n == 0 or len(base[0]) == 0:
            return base
        T = len(base[0])
        L = min(T, max(1, int(round(strength))))
        start = rng.randrange(T - L + 1)
        s = [list(row) for row in base]
        for i in range(n):
            for t in range(start, start + L):
                if rng.random() < self.keep_prob:
                    continue
                s[i][t] = rng.random() < self.open_prob
        new = canonical(s)
        if new == base:
            i = rng.randrange(n)
            t = rng.randrange(start, start + L)
            s[i][t] = not s[i][t]
            new = canonical(s)
        return new


def build_component(problem, open_prob: float = 0.6, keep_prob: float = 0.3):
    return PeriodWindowReshuffle(problem, open_prob=open_prob, keep_prob=keep_prob)
