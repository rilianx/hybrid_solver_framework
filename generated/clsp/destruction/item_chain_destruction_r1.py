from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "item_chain_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.9]},
    },
}


class ItemChainDestruction:
    """Libera todos los setups de algunos ítems completos, rompiendo cadenas temporales."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        target = max(1, int(round(ratio * total_vars)))

        items = list(range(n_items))
        items.sort(key=lambda i: (
            sum(1 for t in range(n_periods) if sol[i][t]),
            self.inst.setup_cost[i],
        ))

        free_vars = set()
        for i in items:
            period_order = list(range(n_periods))
            rng.shuffle(period_order)
            for t in period_order:
                free_vars.add(var_name(i, t))
                if len(free_vars) >= target:
                    break
            if len(free_vars) >= target:
                break

        if not free_vars:
            free_vars.add(var_name(rng.randrange(n_items), rng.randrange(n_periods)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.3):
    return ItemChainDestruction(problem, problem.inst)
