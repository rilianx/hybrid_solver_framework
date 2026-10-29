from random import Random

COMPONENT = {
    "name": "shaw_relatedness_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "determinism": {"type": "float", "range": [1.0, 12.0]},
        "route_weight": {"type": "float", "range": [0.0, 1.0]},
        "demand_weight": {"type": "float", "range": [0.0, 1.0]},
    },
}


class ShawRelatednessArcDestruction:
    """Remoción tipo Shaw: semilla aleatoria y luego clientes con alta relación
    (distancia normalizada + misma ruta + demanda similar) a alguno ya removido.
    Libera todos los arcos incidentes a los clientes removidos."""

    def __init__(self, problem, inst, determinism, route_weight, demand_weight):
        self.problem = problem
        self.inst = inst
        self.p = float(determinism)
        self.rw = float(route_weight)
        self.dw = float(demand_weight)
        custs = list(inst.customers)
        maxd = 0.0
        for a in [0] + custs:
            for b in custs:
                if a != b:
                    d = inst.dist(a, b)
                    if d > maxd:
                        maxd = d
        self.maxd = maxd if maxd > 0 else 1.0
        dem = [inst.demand[c] for c in custs] or [0.0]
        span = max(dem) - min(dem)
        self.dspan = span if span > 0 else 1.0

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

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        assignment = self.problem.to_assignment(sol)
        custs = list(inst.customers)
        n = len(custs)
        if n == 0 or not assignment:
            keys = sorted(assignment)
            free = {keys[0]} if keys else set()
            return {v: x for v, x in assignment.items() if v not in free}, free
        k = max(1, min(n, int(round(ratio * n))))
        route_of = {}
        pred = {}
        succ = {}
        for idx, r in enumerate(sol):
            rl = [int(c) for c in r]
            for i, c in enumerate(rl):
                route_of[c] = idx
                pred[c] = rl[i - 1] if i > 0 else 0
                succ[c] = rl[i + 1] if i + 1 < len(rl) else 0

        def rel(a, b):
            v = inst.dist(a, b) / self.maxd
            if route_of.get(a, -1) != route_of.get(b, -2):
                v += self.rw
            v += self.dw * abs(inst.demand[a] - inst.demand[b]) / self.dspan
            return v

        removed = [rng.choice(custs)]
        removed_set = set(removed)
        while len(removed) < k:
            ref = rng.choice(removed)
            rest = [c for c in custs if c not in removed_set]
            if not rest:
                break
            rest.sort(key=lambda c: (rel(ref, c), c))
            y = rng.random()
            pos = int((y ** self.p) * len(rest))
            pos = min(pos, len(rest) - 1)
            c = rest[pos]
            removed.append(c)
            removed_set.add(c)
        # Clúster: clientes relacionados + sus vecinos de ruta + depósito.
        cluster = set(removed_set)
        cluster.add(0)
        for c in removed_set:
            cluster.add(pred.get(c, 0))
            cluster.add(succ.get(c, 0))
        free_vars = self._induced_arcs(cluster, assignment)
        if not free_vars:
            free_vars = {sorted(assignment)[0]}
        partial = {v: x for v, x in assignment.items() if v not in free_vars}
        return partial, free_vars

    def _induced_arcs(self, nodes, assignment):
        free = set()
        nl = sorted(nodes)
        for a in nl:
            for b in nl:
                if a == b:
                    continue
                v = f"x_{a}_{b}"
                if v in assignment:
                    free.add(v)
        return free


def build_component(problem, determinism=5.0, route_weight=0.3, demand_weight=0.1):
    return ShawRelatednessArcDestruction(problem, problem.inst, determinism,
                                         route_weight, demand_weight)
