from random import Random

from generated.clsp_setups_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "random_setup_flip_k",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"scale": {"type": "float", "range": [0.5, 3.0]}},
}


class RandomSetupFlipK:
    def __init__(self, problem, scale=1.0):
        self.problem = problem
        self.n = problem.inst.n_items
        self.T = problem.inst.n_periods
        self.scale = float(scale)

    def perturb(self, sol, strength: float, rng: Random):
        n, T = self.n, self.T
        N = n * T
        if N == 0:
            return canonical(sol)
        k = max(1, min(N, int(round(strength * self.scale))))
        plan = [list(r) for r in canonical(sol)]
        for c in rng.sample(range(N), k):
            i, t = divmod(c, T)
            plan[i][t] = not plan[i][t]
        return canonical(plan)


def build_component(problem, scale=1.0):
    return RandomSetupFlipK(problem, scale=scale)
