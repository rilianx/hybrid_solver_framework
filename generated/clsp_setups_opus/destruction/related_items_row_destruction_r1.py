from random import Random

from generated.clsp_setups_cycle.model.parts import canonical

COMPONENT = {
    "name": "related_items_row_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "determinism": {"type": "float", "range": [1.0, 10.0]},
    },
}


class RelatedItemsRowDestruction:
    """Shaw removal sobre ítems: semilla aleatoria y se liberan los planes completos
    de los ítems más parecidos (compiten por los mismos períodos de capacidad)."""

    def __init__(self, problem, determinism: float = 4.0):
        self.problem = problem
        self.inst = problem.inst
        self.determinism = float(determinism)
        inst = self.inst
        n, T = inst.n_items, inst.n_periods

        def norm(vals):
            lo, hi = min(vals), max(vals)
            rng_ = hi - lo
            return [0.0 if rng_ <= 1e-12 else (v - lo) / rng_ for v in vals]

        self.f_st = norm([float(x) for x in inst.setup_time]) if n else []
        self.f_sc = norm([float(x) for x in inst.setup_cost]) if n else []
        self.f_h = norm([float(x) for x in inst.holding_cost]) if n else []
        self.profile = []
        for i in range(n):
            row = [max(0.0, float(inst.demand[i][t])) for t in range(T)]
            s = sum(row)
            self.profile.append([r / s for r in row] if s > 0 else [0.0] * T)

    def _relatedness(self, a, b):
        d = abs(self.f_st[a] - self.f_st[b]) + abs(self.f_sc[a] - self.f_sc[b]) + abs(self.f_h[a] - self.f_h[b])
        overlap = sum(min(x, y) for x, y in zip(self.profile[a], self.profile[b]))
        return d + (1.0 - overlap)  # menor = más relacionado

    def destroy(self, sol, ratio: float, rng: Random):
        sol = canonical(sol)
        assignment = self.problem.to_assignment(sol)
        keys = list(assignment.keys())
        n, T = self.inst.n_items, self.inst.n_periods
        total = len(keys)
        k = min(total, max(1, int(round(ratio * total))))

        free_vars = set()
        if n > 0 and T > 0:
            seed = rng.randrange(n)
            remaining = [i for i in range(n) if i != seed]
            order = [seed]
            while remaining:
                remaining.sort(key=lambda j: self._relatedness(seed, j))
                idx = int((rng.random() ** self.determinism) * len(remaining))
                order.append(remaining.pop(min(idx, len(remaining) - 1)))
            for i in order:
                need = k - len(free_vars)
                if need <= 0:
                    break
                if need >= T:
                    seg = range(T)
                else:
                    st = rng.randint(0, T - need)
                    seg = range(st, st + need)
                for t in seg:
                    name = f"y_{i}_{t}"
                    if name in assignment:
                        free_vars.add(name)
        if not free_vars:
            free_vars.add(rng.choice(keys))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, determinism: float = 4.0, **params):
    return RelatedItemsRowDestruction(problem, determinism=determinism)
