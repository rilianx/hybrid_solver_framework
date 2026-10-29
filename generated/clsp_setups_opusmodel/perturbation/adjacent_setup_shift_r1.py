from random import Random

from generated.clsp_setups_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "adjacent_setup_shift",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"merge_prob": {"type": "float", "range": [0.0, 0.5]}},
}


class AdjacentSetupShift:
    def __init__(self, problem, merge_prob=0.2):
        self.problem = problem
        self.n = problem.inst.n_items
        self.T = problem.inst.n_periods
        self.merge_prob = float(merge_prob)

    def perturb(self, sol, strength: float, rng: Random):
        n, T = self.n, self.T
        base = canonical(sol)
        if n * T == 0:
            return base
        plan = [list(r) for r in base]
        k = max(1, int(round(strength)))
        for _ in range(k):
            on_cells = [(i, t) for i in range(n) for t in range(T) if plan[i][t]]
            if not on_cells or T < 2:
                i, t = rng.randrange(n), rng.randrange(T)
                plan[i][t] = not plan[i][t]
                continue
            i, t = rng.choice(on_cells)
            dirs = [dt for dt in (-1, 1) if 0 <= t + dt < T]
            dt = rng.choice(dirs)
            u = t + dt
            if plan[i][u]:
                # el vecino ya tiene setup: fusionar lotes (eliminar este) con cierta probabilidad
                if rng.random() < self.merge_prob or len(dirs) == 1:
                    plan[i][t] = False
                else:
                    other = t - dt
                    if 0 <= other < T and not plan[i][other]:
                        plan[i][t] = False
                        plan[i][other] = True
                    else:
                        plan[i][t] = False
            else:
                plan[i][t] = False
                plan[i][u] = True
        out = canonical(plan)
        if out == base:
            i, t = rng.randrange(n), rng.randrange(T)
            plan[i][t] = not plan[i][t]
            out = canonical(plan)
        return out


def build_component(problem, merge_prob=0.2):
    return AdjacentSetupShift(problem, merge_prob=merge_prob)
