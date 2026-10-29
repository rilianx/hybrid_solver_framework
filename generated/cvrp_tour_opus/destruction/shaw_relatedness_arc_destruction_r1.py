from random import Random

from generated.cvrp_tour_cycle.model.parts import canonical  # noqa: F401

COMPONENT = {
    "name": "shaw_relatedness_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "demand_weight": {"type": "float", "range": [0.0, 1.0]},
        "route_weight": {"type": "float", "range": [0.0, 1.0]},
        "determinism": {"type": "float", "range": [1.0, 10.0]},
    },
}


def _parse_routes(assignment):
    succ = {}
    starts = []
    for name, v in assignment.items():
        if v > 0.5:
            _, a, b = name.split("_")
            a, b = int(a), int(b)
            if a == 0:
                starts.append(b)
            else:
                succ[a] = b
    routes, seen = [], set()
    for s in sorted(starts):
        r, cur = [], s
        while cur != 0 and cur not in seen:
            r.append(cur)
            seen.add(cur)
            cur = succ.get(cur, 0)
        if r:
            routes.append(r)
    pred, nxt, route_of = {}, {}, {}
    for idx, r in enumerate(routes):
        for p, c in enumerate(r):
            pred[c] = r[p - 1] if p > 0 else 0
            nxt[c] = r[p + 1] if p + 1 < len(r) else 0
            route_of[c] = idx
    return routes, pred, nxt, route_of


class ShawRelatednessArcDestruction:
    """Selecciona clientes relacionados (distancia, demanda, misma ruta) al estilo Shaw y libera
    todos sus arcos incidentes y los arcos entre sus vecinos para permitir reconexión."""

    def __init__(self, problem, inst, demand_weight, route_weight, determinism):
        self.problem, self.inst = problem, inst
        self.demand_weight = demand_weight
        self.route_weight = route_weight
        self.determinism = determinism

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        assignment = self.problem.to_assignment(sol)
        customers = list(inst.customers)
        n = len(customers)
        nn = inst.n_customers
        if n == 0:
            return {}, set()
        k = max(1, min(n, int(round(max(0.0, ratio) * n))))
        _, pred, nxt, route_of = _parse_routes(assignment)

        maxd = max((inst.dist(0, c) for c in customers), default=1.0) * 2.0 or 1.0
        maxdem = max((inst.demand[c] for c in customers), default=1.0) or 1.0

        def rel(a, b):
            r = inst.dist(a, b) / maxd
            r += self.demand_weight * abs(inst.demand[a] - inst.demand[b]) / maxdem
            if route_of.get(a, -1) != route_of.get(b, -2):
                r += self.route_weight
            return r

        selected = [rng.choice(customers)]
        remaining = [c for c in customers if c != selected[0]]
        while len(selected) < k and remaining:
            ref = rng.choice(selected)
            remaining.sort(key=lambda c: rel(ref, c))
            idx = int((rng.random() ** self.determinism) * len(remaining))
            idx = min(idx, len(remaining) - 1)
            selected.append(remaining.pop(idx))

        S = set(selected)
        A = set(S) | {0}
        for c in S:
            A.add(pred.get(c, 0))
            A.add(nxt.get(c, 0))

        free_vars = set()
        for i in range(nn + 1):
            for j in range(nn + 1):
                if i == j:
                    continue
                if i in S or j in S or (i in A and j in A):
                    name = f"x_{i}_{j}"
                    if name in assignment:
                        free_vars.add(name)
        if not free_vars:
            free_vars.add(next(iter(assignment)))
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, demand_weight=0.3, route_weight=0.2, determinism=4.0):
    return ShawRelatednessArcDestruction(problem, problem.inst, demand_weight, route_weight, determinism)
