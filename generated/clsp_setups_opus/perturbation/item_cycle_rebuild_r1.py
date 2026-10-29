from random import Random

from generated.clsp_setups_cycle.model.parts import canonical

COMPONENT = {
    "name": "item_cycle_rebuild",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "max_cycle": {"type": "int", "range": [2, 8]},
        "anchor_first_demand": {"type": "bool"},
    },
}


class ItemCycleRebuild:
    def __init__(self, problem, max_cycle: int = 4, anchor_first_demand: bool = True):
        self.problem = problem
        self.max_cycle = int(max_cycle)
        self.anchor_first_demand = bool(anchor_first_demand)
        inst = problem.inst
        self.first_dem = []
        for i in range(inst.n_items):
            fd = None
            for t in range(inst.n_periods):
                if float(inst.demand[i][t]) > 1e-9:
                    fd = t
                    break
            self.first_dem.append(fd)

    def _cycle_row(self, i, T, rng):
        p = rng.randint(1, max(1, min(self.max_cycle, T)))
        fd = self.first_dem[i] if i < len(self.first_dem) else None
        if self.anchor_first_demand and fd is not None:
            offset = fd
        else:
            offset = rng.randrange(p)
        row = [t >= offset and (t - offset) % p == 0 for t in range(T)]
        if self.anchor_first_demand and fd is not None:
            row[fd] = True
        return row

    def perturb(self, sol, strength: float, rng: Random):
        base = canonical(sol)
        n = len(base)
        if n == 0 or len(base[0]) == 0:
            return base
        T = len(base[0])
        k = min(n, max(1, int(round(strength))))
        s = [list(row) for row in base]
        for i in rng.sample(range(n), k):
            new_row = s[i]
            for _ in range(5):
                new_row = self._cycle_row(i, T, rng)
                if new_row != list(base[i]):
                    break
            s[i] = new_row
        new = canonical(s)
        if new == base:
            i = rng.randrange(n)
            cand = [t for t in range(T) if t != self.first_dem[i]] if i < len(self.first_dem) else []
            t = rng.choice(cand) if cand else rng.randrange(T)
            s[i][t] = not s[i][t]
            new = canonical(s)
        return new


def build_component(problem, max_cycle: int = 4, anchor_first_demand: bool = True):
    return ItemCycleRebuild(problem, max_cycle=max_cycle, anchor_first_demand=anchor_first_demand)
