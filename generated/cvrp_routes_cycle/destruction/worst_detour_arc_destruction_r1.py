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

    def _free_arcs(self, nodes):
        n = self.inst.n_customers
        free = set()
        if self.scope == "internal":
            ns = set(nodes) | {0}
            for i in ns:
                for j in ns:
                    if i != j:
                        free.add(f"x_{i}_{j}")
        else:
            for a in nodes:
                for j in range(n + 1):
                    if j != a:
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
            savings.setdefault(c, float("inf"))  # clientes no visitados: prioridad máxima
        k = max(1, min(n, int(round(float(ratio) * n))))
        pool = sorted(customers, key=lambda c: -savings[c])
        chosen = set()
        while len(chosen) < k and pool:
            idx = int(len(pool) * (rng.random() ** self.p))
            idx = min(idx, len(pool) - 1)
            chosen.add(pool.pop(idx))
        nodes = set(chosen)
        if self.expand:
            for c in chosen:
                for nb in (pred.get(c, 0), succ.get(c, 0)):
                    if nb != 0:
                        nodes.add(nb)
        free_vars = self._free_arcs(nodes) & set(assignment.keys())
        if not free_vars:
            free_vars = {rng.choice(sorted(assignment.keys()))}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, determinism=4.0, scope="incident", expand_neighbors=True):
    return WorstDetourArcDestruction(problem, problem.inst, determinism, scope, expand_neighbors)
