from random import Random

COMPONENT = {
    "name": "whole_item_release_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "focus_on_cost": {"type": "bool", "range": [0, 1]},
    },
}


class WholeItemReleaseDestruction:
    """Libera todos los setups de unos pocos ítems completos para reoptimizar su patrón temporal."""

    def __init__(self, problem, inst, focus_on_cost: bool = True):
        self.problem = problem
        self.inst = inst
        self.focus_on_cost = focus_on_cost

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        target = max(1, int(round(ratio * n_items * n_periods)))

        scores = []
        for i in range(n_items):
            active = sum(1 for t in range(n_periods) if sol[i][t])
            if self.focus_on_cost:
                score = self.inst.setup_cost[i] / max(1, active)
            else:
                score = active
            scores.append((score, i))
        scores.sort(reverse=True)

        free_vars = set()
        chosen_items = []
        for _, i in scores:
            chosen_items.append(i)
            for t in range(n_periods):
                if sol[i][t]:
                    free_vars.add(f"y_{i}_{t}")
            if len(free_vars) >= target:
                break

        if len(free_vars) < target:
            remaining = [f"y_{i}_{t}" for i in range(n_items) for t in range(n_periods) if f"y_{i}_{t}" not in free_vars]
            rng.shuffle(remaining)
            for v in remaining:
                free_vars.add(v)
                if len(free_vars) >= target:
                    break

        if not free_vars:
            free_vars.add(next(iter(assignment.keys())))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, focus_on_cost: bool = True):
    return WholeItemReleaseDestruction(problem, problem.inst, focus_on_cost=focus_on_cost)
