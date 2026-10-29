from random import Random

from generated.clsp_setups_cycle.model.parts import canonical

COMPONENT = {
    "name": "wasteful_cell_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "greediness": {"type": "float", "range": [0.5, 4.0]},
        "neighbor_prob": {"type": "float", "range": [0.0, 1.0]},
    },
}


class WastefulCellDestruction:
    """Puntúa cada celda (i,t) por su ineficiencia estimada:
    - setup activo: s_i / (d_it + ε·d̄_i)   (setup caro que cubre poca demanda propia)
    - sin setup: h_i · d_it · gap          (demanda servida desde un setup lejano)
    Muestreo ponderado sin reemplazo (Efraimidis-Spirakis) y expansión a t±1."""

    def __init__(self, problem, greediness: float = 1.5, neighbor_prob: float = 0.4):
        self.problem = problem
        self.inst = problem.inst
        self.greediness = float(greediness)
        self.neighbor_prob = float(neighbor_prob)

    def _scores(self, sol):
        inst = self.inst
        n, T = inst.n_items, inst.n_periods
        act, inact = {}, {}
        for i in range(n):
            dem = [max(0.0, float(inst.demand[i][t])) for t in range(T)]
            dbar = (sum(dem) / T) if T else 0.0
            eps = 0.1 * dbar + 1e-6
            s, h = float(inst.setup_cost[i]), float(inst.holding_cost[i])
            last = None
            for t in range(T):
                if sol[i][t]:
                    act[(i, t)] = s / (dem[t] + eps)
                    last = t
                else:
                    gap = (t - last) if last is not None else T  # sin setup previo: muy malo
                    inact[(i, t)] = h * dem[t] * gap + 1e-9
        out = {}
        for grp in (act, inact):
            if grp:
                mx = max(grp.values()) or 1.0
                for c, v in grp.items():
                    out[c] = (v / mx) + 1e-3
        return out

    def destroy(self, sol, ratio: float, rng: Random):
        sol = canonical(sol)
        assignment = self.problem.to_assignment(sol)
        keys = list(assignment.keys())
        T = self.inst.n_periods
        total = len(keys)
        k = min(total, max(1, int(round(ratio * total))))

        scores = self._scores(sol)
        keyed = []
        for (i, t), w in scores.items():
            u = rng.random()
            keyed.append((u ** (1.0 / (w ** self.greediness)), i, t))
        keyed.sort(reverse=True)

        free_vars = set()
        for _, i, t in keyed:
            if len(free_vars) >= k:
                break
            name = f"y_{i}_{t}"
            if name in assignment:
                free_vars.add(name)
            for dt in (-1, 1):
                if len(free_vars) >= k:
                    break
                tt = t + dt
                if 0 <= tt < T and rng.random() < self.neighbor_prob:
                    nb = f"y_{i}_{tt}"
                    if nb in assignment:
                        free_vars.add(nb)
        if not free_vars:
            free_vars.add(rng.choice(keys))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, greediness: float = 1.5, neighbor_prob: float = 0.4, **params):
    return WastefulCellDestruction(problem, greediness=greediness, neighbor_prob=neighbor_prob)
