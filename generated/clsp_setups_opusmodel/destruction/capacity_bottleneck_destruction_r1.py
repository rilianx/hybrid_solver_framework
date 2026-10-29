from random import Random

from generated.clsp_setups_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "capacity_bottleneck_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.parts"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "spread": {"type": "int", "range": [0, 3]},
    },
}


class CapacityBottleneckDestruction:
    """Calcula la utilización de capacidad de cada período (producción + tiempos de setup) y
    selecciona períodos por ruleta proporcional a su utilización. Para cada período elegido libera
    todos sus setups y, en los períodos vecinos (±spread), los de los ítems con setup o demanda allí,
    para permitir desplazar producción fuera del cuello de botella."""

    def __init__(self, problem, inst, spread):
        self.problem, self.inst, self.spread = problem, inst, spread

    def _utilization(self, plan):
        inst = self.inst
        n, T = inst.n_items, inst.n_periods
        aux = None
        parts = getattr(self.problem, "parts", None)
        if parts is not None and hasattr(parts, "aux_values"):
            try:
                aux = parts.aux_values(inst, plan)
            except Exception:
                aux = None
        util = []
        for t in range(T):
            load = 0.0
            for i in range(n):
                if plan[i][t]:
                    load += float(inst.setup_time[i])
                    if aux is not None:
                        load += float(aux.get(f"x_{i}_{t}", 0.0))
                    else:
                        load += float(inst.demand[i][t])
            c = float(inst.capacity[t])
            util.append(load / c if c > 1e-12 else 1.0)
        return util

    def destroy(self, sol, ratio: float, rng: Random):
        plan = canonical(sol)
        assignment = self.problem.to_assignment(plan)
        inst = self.inst
        n, T = inst.n_items, inst.n_periods
        total = n * T
        k = max(1, min(total, int(round(ratio * total))))
        util = self._utilization(plan)
        weights = {t: max(util[t], 0.0) + 0.05 for t in range(T)}
        ordered = []
        seen = set()

        def push(i, t):
            if (i, t) not in seen:
                seen.add((i, t))
                ordered.append((i, t))

        while weights and len(ordered) < k:
            tot = sum(weights.values())
            r = rng.random() * tot
            acc = 0.0
            pick = None
            for t in sorted(weights):
                acc += weights[t]
                if r <= acc:
                    pick = t
                    break
            if pick is None:
                pick = max(weights)
            del weights[pick]
            center = list(range(n))
            rng.shuffle(center)
            for i in center:
                push(i, pick)
            for dist in range(1, self.spread + 1):
                for tt in (pick - dist, pick + dist):
                    if 0 <= tt < T:
                        for i in center:
                            if plan[i][tt] or float(inst.demand[i][tt]) > 1e-9:
                                push(i, tt)
        chosen = ordered[:k]
        free_vars = {f"y_{i}_{t}" for i, t in chosen if f"y_{i}_{t}" in assignment}
        if not free_vars:
            free_vars = {rng.choice(sorted(assignment))}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2, spread: int = 1):
    return CapacityBottleneckDestruction(problem, problem.inst, spread)
