from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "whole_item_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class WholeItemDestruction:
    """Libera ítems completos: todos sus setups pasan a ser decididos por la reparación."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods

        # Score estructural: ítems con más setups activos y más demanda total son más "influyentes".
        item_scores = []
        for i in range(n_items):
            active = sum(1 for t in range(n_periods) if sol[i][t])
            demand_mass = sum(self.inst.demand[i])
            score = active * 1000.0 + demand_mass
            item_scores.append((score, i))
        item_scores.sort(reverse=True)

        target_vars = max(1, int(round(ratio * n_items * n_periods)))

        chosen_items = []
        freed = 0
        for _, i in item_scores:
            chosen_items.append(i)
            freed += n_periods
            if freed >= target_vars:
                break

        free_vars = {var_name(i, t) for i in chosen_items for t in range(n_periods)}

        # Garantía: si por alguna razón no hubiera setups de esos ítems, liberamos al menos uno real.
        if not free_vars:
            candidates = [(i, t) for i in range(n_items) for t in range(n_periods) if sol[i][t]]
            if candidates:
                i, t = rng.choice(candidates)
                free_vars = {var_name(i, t)}
            else:
                free_vars = {var_name(0, 0)}

        # Ajuste fino: si liberamos demasiado poco por ítems vacíos, completamos con setups activos aleatorios.
        if len(free_vars) < 1:
            free_vars.add(var_name(0, 0))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25):
    return WholeItemDestruction(problem, problem.inst)
