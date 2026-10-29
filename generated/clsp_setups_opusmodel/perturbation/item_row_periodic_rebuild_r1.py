from random import Random

from generated.clsp_setups_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "item_row_periodic_rebuild",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "max_period": {"type": "int", "range": [1, 8]},
        "repair": {"type": "bool"},
    },
}


class ItemRowPeriodicRebuild:
    def __init__(self, problem, max_period=4, repair=True):
        self.problem = problem
        inst = problem.inst
        self.n = inst.n_items
        self.T = inst.n_periods
        self.demand = inst.demand
        self.max_period = max(1, int(max_period))
        self.repair = bool(repair)

    def _row(self, i, rng):
        T = self.T
        first = next((t for t in range(T) if self.demand[i][t] > 1e-9), None)
        row = [False] * T
        if first is None:
            return row
        p = rng.randint(1, max(1, min(self.max_period, T)))
        t = first
        while t < T:
            row[t] = True
            t += p
        return row

    def perturb(self, sol, strength: float, rng: Random):
        n, T = self.n, self.T
        base = canonical(sol)
        if n * T == 0:
            return base
        k = max(1, min(n, int(round(strength))))
        items = rng.sample(range(n), k)
        plan = [list(r) for r in base]
        for i in items:
            plan[i] = self._row(i, rng)
        if self.repair:
            tries = k * T
            while tries > 0 and not self.problem.is_feasible(canonical(plan)):
                tries -= 1
                cand = [(i, t) for i in items for t in range(T)
                        if not plan[i][t] and self.demand[i][t] > 1e-9]
                if not cand:
                    break
                i, t = rng.choice(cand)
                plan[i][t] = True
        out = canonical(plan)
        if out == base:
            i = rng.choice(items)
            t = rng.randrange(T)
            plan[i][t] = not plan[i][t]
            out = canonical(plan)
        return out


def build_component(problem, max_period=4, repair=True):
    return ItemRowPeriodicRebuild(problem, max_period=max_period, repair=repair)
