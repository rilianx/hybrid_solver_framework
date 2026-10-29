from random import Random

from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "spatial_cluster_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "noise": {"type": "float", "range": [0.0, 0.5]},
        "scope": {"type": "cat", "values": ["incident", "internal"]},
        "expand_neighbors": {"type": "bool"},
    },
}


class SpatialClusterArcDestruction:
    """Elige un cliente semilla y libera los k clientes más cercanos (con ruido).

    Se liberan los arcos incidentes (o internos) al conjunto de clientes elegidos,
    opcionalmente ampliado con sus predecesores/sucesores en la ruta actual.
    """

    def __init__(self, problem, inst, noise=0.15, scope="incident", expand_neighbors=True):
        self.problem = problem
        self.inst = inst
        self.noise = float(noise)
        self.scope = scope
        self.expand = bool(expand_neighbors)

    def _neighbors(self, routes):
        pred, succ = {}, {}
        for r in routes:
            for idx, c in enumerate(r):
                pred[c] = r[idx - 1] if idx > 0 else 0
                succ[c] = r[idx + 1] if idx + 1 < len(r) else 0
        return pred, succ

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
        customers = list(self.inst.customers)
        n = len(customers)
        if n == 0 or not assignment:
            return dict(assignment), set()
        k = max(1, min(n, int(round(float(ratio) * n))))
        seed = rng.choice(customers)
        scored = []
        for c in customers:
            d = self.inst.dist(seed, c)
            scored.append((d * (1.0 + self.noise * rng.random()), c))
        scored.sort()
        chosen = {c for _, c in scored[:k]}
        nodes = set(chosen)
        if self.expand:
            pred, succ = self._neighbors(routes)
            for c in chosen:
                for nb in (pred.get(c, 0), succ.get(c, 0)):
                    if nb != 0:
                        nodes.add(nb)
        free_vars = self._free_arcs(nodes) & set(assignment.keys())
        if not free_vars:
            free_vars = {rng.choice(sorted(assignment.keys()))}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, noise=0.15, scope="incident", expand_neighbors=True):
    return SpatialClusterArcDestruction(problem, problem.inst, noise, scope, expand_neighbors)
