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
        loads = self._loads(plan)
        ordered = []
        seen = set()

        def push(i, t):
            if (i, t) not in seen and len(ordered) < k:
                seen.add((i, t))
                ordered.append((i, t))

        def roulette(wdict):
            tot = sum(wdict.values())
            r = rng.random() * tot
            acc = 0.0
            for key in sorted(wdict):
                acc += wdict[key]
                if r <= acc:
                    return key
            return max(wdict)

        n_slack = self.spread + 1
        weights = {t: max(util[t], 0.0) ** 2 + 0.02 for t in range(T)}
        while weights and len(ordered) < k:
            p = roulette(weights)
            del weights[p]
            # items cargando el período p, elegidos por ruleta según su carga
            iw = {i: loads[i][p] + 1e-3 for i in range(n) if plan[i][p]}
            if not iw:
                iw = {i: 1.0 for i in range(n) if float(inst.demand[i][p]) > 1e-9}
            n_items_pick = max(1, len(iw) // 2)
            for _ in range(n_items_pick):
                if not iw or len(ordered) >= k:
                    break
                i = roulette(iw)
                del iw[i]
                push(i, p)
                # períodos anteriores con holgura donde anticipar la producción de i
                earlier = [t for t in range(p) if (i, t) not in seen]
                earlier.sort(key=lambda t: (util[t], -t, rng.random()))
                for t in earlier[:n_slack]:
                    push(i, t)
        if len(ordered) < k:
            rest = [(i, t) for i in range(n) for t in range(T) if (i, t) not in seen]
            rng.shuffle(rest)
            for c in rest[: k - len(ordered)]:
                push(*c)
        chosen = ordered[:k]
        free_vars = {f"y_{i}_{t}" for i, t in chosen if f"y_{i}_{t}" in assignment}
        if not free_vars:
            free_vars = {rng.choice(sorted(assignment))}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars

    def _loads(self, plan):
        inst = self.inst
        n, T = inst.n_items, inst.n_periods
        aux = None
        parts = getattr(self.problem, "parts", None)
        if parts is not None and hasattr(parts, "aux_values"):
            try:
                aux = parts.aux_values(inst, plan)
            except Exception:
                aux = None
        loads = [[0.0] * T for _ in range(n)]
        for i in range(n):
            for t in range(T):
                if plan[i][t]:
                    v = float(inst.setup_time[i])
                    if aux is not None:
                        v += float(aux.get(f"x_{i}_{t}", 0.0))
                    else:
                        v += float(inst.demand[i][t])
                    loads[i][t] = v
        return loads


def build_component(problem, ratio: float = 0.2, spread: int = 1):
    return CapacityBottleneckDestruction(problem, problem.inst, spread)
