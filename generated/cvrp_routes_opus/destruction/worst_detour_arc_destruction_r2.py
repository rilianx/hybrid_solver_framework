from random import Random

from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "worst_detour_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "determinism": {"type": "float", "range": [1.0, 10.0]},
        "scope": {"type": "cat", "values": ["incident", "internal"]},
        "expand_neighbors": {"type": "bool"},
    },
}


_NN_BASE = 4


class WorstDetourArcDestruction:
    """Ordena clientes por el ahorro que produciría quitarlos de su ruta y elige
    k de ellos con sesgo hacia los peores (índice = floor(L * u^p)). Libera los
    arcos asociados a los clientes elegidos (y sus vecinos de ruta si se pide)."""

    def __init__(self, problem, inst, determinism=4.0, scope="incident", expand_neighbors=True):
        self.problem = problem
        self.inst = inst
        self.p = float(determinism)
        self.scope = scope
        self.expand = bool(expand_neighbors)

    def _free_arcs(self, nodes, pred, succ):
        """Libera un conjunto disperso: para cada cliente elegido, sus arcos actuales
        (pred->c, c->succ), los arcos con el depósito y los arcos hacia sus m vecinos
        más cercanos (en ambos sentidos). En modo 'internal' los vecinos se restringen
        a los propios clientes elegidos (re-enlace entre los peores clientes)."""
        n = self.inst.n_customers
        dist = self.inst.dist
        m = _NN_BASE + (2 if self.expand else 0)
        free = set()
        node_set = set(nodes)
        for a in nodes:
            p = pred.get(a, 0)
            s = succ.get(a, 0)
            free.add(f"x_{p}_{a}")
            free.add(f"x_{a}_{s}")
            free.add(f"x_0_{a}")
            free.add(f"x_{a}_0")
            if self.scope == "internal":
                cands = [j for j in node_set if j != a]
            else:
                cands = [j for j in range(1, n + 1) if j != a]
            cands.sort(key=lambda j: (dist(a, j), j))
            for j in cands[:m]:
                free.add(f"x_{a}_{j}")
                free.add(f"x_{j}_{a}")
        return free

    def destroy(self, sol, ratio: float, rng: Random):
        routes = canonical(sol)
        assignment = self.problem.to_assignment(routes)
        n_c = self.inst.n_customers
        dist = self.inst.dist
        pred, succ, savings = {}, {}, {}
        for r in routes:
            rr = [c for c in r if 1 <= c <= n_c]
            for idx, c in enumerate(rr):
                p = rr[idx - 1] if idx > 0 else 0
                s = rr[idx + 1] if idx + 1 < len(rr) else 0
                pred[c], succ[c] = p, s
                sv = dist(p, c) + dist(c, s) - dist(p, s)
                savings[c] = max(savings.get(c, sv), sv)
        customers = list(self.inst.customers)
        n = len(customers)
        if n == 0 or not assignment:
            return dict(assignment), set()
        for c in customers:
            savings.setdefault(c, float("inf"))
        k = max(1, min(n, int(round(float(ratio) * n))))
        pool = sorted(customers, key=lambda c: (-savings[c], c))
        chosen = []
        while len(chosen) < k and pool:
            idx = int(len(pool) * (rng.random() ** self.p))
            idx = min(idx, len(pool) - 1)
            chosen.append(pool.pop(idx))
        free_vars = self._free_arcs(chosen, pred, succ) & set(assignment.keys())
        if not free_vars:
            free_vars = {rng.choice(sorted(assignment.keys()))}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, determinism=4.0, scope="incident", expand_neighbors=True):
    return WorstDetourArcDestruction(problem, problem.inst, determinism, scope, expand_neighbors)
