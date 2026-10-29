import math
from random import Random

COMPONENT = {
    "name": "route_cluster_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "partial_last": {"type": "bool"},
        "seed_mode": {"type": "cat", "values": ["random", "worst_avg_cost"]},
    },
}


class RouteClusterArcDestruction:
    """Selecciona una ruta semilla (al azar o la de mayor costo por cliente) y añade
    rutas enteras ordenadas por cercanía de centroides hasta cubrir ~ratio·n clientes.
    Libera todos los arcos incidentes a los clientes de esas rutas."""

    def __init__(self, problem, inst, partial_last, seed_mode):
        self.problem = problem
        self.inst = inst
        self.partial_last = bool(partial_last)
        self.seed_mode = seed_mode

    def _free_arcs(self, nodes, assignment):
        N = self.inst.n_customers + 1
        free = set()
        for t in nodes:
            for k in range(N):
                if k == t:
                    continue
                a = f"x_{t}_{k}"
                b = f"x_{k}_{t}"
                if a in assignment:
                    free.add(a)
                if b in assignment:
                    free.add(b)
        return free

    def _centroid(self, r):
        xs = [self.inst.coords[c][0] for c in r]
        ys = [self.inst.coords[c][1] for c in r]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def _route_cost(self, r):
        prev, tot = 0, 0.0
        for c in r:
            tot += self.inst.dist(prev, c)
            prev = c
        return tot + self.inst.dist(prev, 0)

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        assignment = self.problem.to_assignment(sol)
        n = inst.n_customers
        routes = [tuple(int(c) for c in r if 1 <= int(c) <= n) for r in sol]
        routes = [r for r in routes if r]
        if n == 0 or not routes or not assignment:
            keys = sorted(assignment)
            free = {keys[0]} if keys else set()
            return {v: x for v, x in assignment.items() if v not in free}, free
        k = max(1, min(n, int(round(ratio * n))))
        if self.seed_mode == "worst_avg_cost":
            scored = sorted(range(len(routes)),
                            key=lambda i: -self._route_cost(routes[i]) / len(routes[i]))
            top = scored[:max(1, min(3, len(scored)))]
            seed = rng.choice(top)
        else:
            seed = rng.randrange(len(routes))
        cs = self._centroid(routes[seed])
        others = [i for i in range(len(routes)) if i != seed]
        others.sort(key=lambda i: (math.hypot(self._centroid(routes[i])[0] - cs[0],
                                              self._centroid(routes[i])[1] - cs[1]),
                                   rng.random()))
        removed = set(routes[seed])
        for i in others:
            if len(removed) >= k:
                break
            r = routes[i]
            if self.partial_last and len(removed) + len(r) > k:
                need = k - len(removed)
                part = sorted(r, key=lambda c: (math.hypot(inst.coords[c][0] - cs[0],
                                                           inst.coords[c][1] - cs[1]), c))
                removed.update(part[:need])
                break
            removed.update(r)
        # Rutas no listadas (p.ej. clientes ausentes en sol) se ignoran; se garantiza >=1 libre.
        free_vars = self._free_arcs(removed, assignment)
        if not free_vars:
            free_vars = {sorted(assignment)[0]}
        partial = {v: x for v, x in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, partial_last=True, seed_mode="random"):
    return RouteClusterArcDestruction(problem, problem.inst, partial_last, seed_mode)
