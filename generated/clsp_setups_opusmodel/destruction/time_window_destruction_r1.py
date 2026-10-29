from random import Random

from generated.clsp_setups_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "time_window_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class TimeWindowDestruction:
    """Libera las variables y_i_t de una ventana contigua de períodos (todas las filas de ítems).

    Si la ventana tiene más celdas que las pedidas, se recorta al azar dentro de la ventana."""

    def __init__(self, problem, inst):
        self.problem, self.inst = problem, inst

    def destroy(self, sol, ratio: float, rng: Random):
        plan = canonical(sol)
        assignment = self.problem.to_assignment(plan)
        n, T = self.inst.n_items, self.inst.n_periods
        total = n * T
        k = max(1, min(total, int(round(ratio * total))))
        w = max(1, min(T, -(-k // n)))
        start = rng.randrange(0, T - w + 1)
        cells = [(i, t) for t in range(start, start + w) for i in range(n)]
        rng.shuffle(cells)
        chosen = cells[:k]
        free_vars = {f"y_{i}_{t}" for i, t in chosen if f"y_{i}_{t}" in assignment}
        if not free_vars:
            free_vars = {rng.choice(sorted(assignment))}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return TimeWindowDestruction(problem, problem.inst)
