from random import Random

from generated.clsp_setups_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "costly_item_rows_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.parts"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "noise": {"type": "float", "range": [0.0, 1.0]},
    },
}


class CostlyItemRowsDestruction:
    """Ordena los ítems por su contribución al costo (setups pagados + inventario retenido),
    perturbada con ruido multiplicativo, y libera filas completas de ítems hasta cubrir el cupo.
    El último ítem puede liberarse solo en un tramo contiguo para no exceder el cupo."""

    def __init__(self, problem, inst, noise):
        self.problem, self.inst, self.noise = problem, inst, noise

    def _item_scores(self, plan):
        inst = self.inst
        n, T = inst.n_items, inst.n_periods
        inv = [0.0] * n
        parts = getattr(self.problem, "parts", None)
        aux = None
        if parts is not None and hasattr(parts, "aux_values"):
            try:
                aux = parts.aux_values(inst, plan)
            except Exception:
                aux = None
        if aux:
            for i in range(n):
                inv[i] = sum(float(aux.get(f"I_{i}_{t}", 0.0)) for t in range(T - 1)) * float(inst.holding_cost[i])
        scores = []
        for i in range(n):
            setups = sum(1 for t in range(T) if plan[i][t])
            scores.append(setups * float(inst.setup_cost[i]) + inv[i])
        return scores

    def destroy(self, sol, ratio: float, rng: Random):
        plan = canonical(sol)
        assignment = self.problem.to_assignment(plan)
        n, T = self.inst.n_items, self.inst.n_periods
        total = n * T
        k = max(1, min(total, int(round(ratio * total))))
        scores = self._item_scores(plan)
        mx = max(scores) if scores else 0.0
        base = mx if mx > 0 else 1.0
        keyed = [((scores[i] + 1e-9 * base) * (1.0 + self.noise * rng.random()) + 1e-12 * rng.random(), i)
                 for i in range(n)]
        keyed.sort(reverse=True)
        free_vars = set()
        for _, i in keyed:
            remaining = k - len(free_vars)
            if remaining <= 0:
                break
            if remaining >= T:
                free_vars.update(f"y_{i}_{t}" for t in range(T))
            else:
                start = rng.randrange(0, T - remaining + 1)
                free_vars.update(f"y_{i}_{t}" for t in range(start, start + remaining))
        free_vars &= set(assignment)
        if not free_vars:
            free_vars = {rng.choice(sorted(assignment))}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2, noise: float = 0.3):
    return CostlyItemRowsDestruction(problem, problem.inst, noise)
