from random import Random

COMPONENT = {
    "name": "route_cluster_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "random_route_prob": {"type": "float", "range": [0.0, 0.5]},
        "overshoot": {"type": "bool", "values": [True, False]},
    },
}


def _xn(i, j):
    return f"x_{i}_{j}"


def _routes(assignment, N):
    succ, pred, starts = {}, {}, []
    for i in range(N):
        for j in range(N):
            if i != j and assignment.get(_xn(i, j), 0.0) > 0.5:
                if i == 0:
                    starts.append(j)
                else:
                    succ.setdefault(i, j)
                if j != 0:
                    pred.setdefault(j, i)
    routes, seen = [], set()
    for s in starts:
        r, c, steps = [], s, 0
        while c != 0 and c not in seen and steps <= N:
            seen.add(c)
            r.append(c)
            c = succ.get(c, 0)
            steps += 1
        if r:
            routes.append(r)
    rest = [c for c in range(1, N) if c not in seen]
    for c in rest:
        routes.append([c])
    return routes, succ, pred


def _free_arcs(S, succ, pred, N, assignment):
    # Bloque intra-clúster: solo arcos entre nodos del clúster (más extremos
    # de corte y depósito). No libera filas/columnas completas de cada
    # cliente: el MIP re-enruta y reparte clientes solo entre las rutas
    # elegidas, sin poder insertarlos en rutas ajenas al clúster.
    A = {0}
    for c in S:
        A.add(c)
        A.add(succ.get(c, 0))
        A.add(pred.get(c, 0))
    free = set()
    for a in A:
        for b in A:
            if a != b:
                free.add(_xn(a, b))
    return {v for v in free if v in assignment}


class RouteClusterDestruction:
    """Libera rutas completas cercanas (por centroide) a una ruta semilla."""

    def __init__(self, problem, inst, random_route_prob, overshoot):
        self.problem, self.inst = problem, inst
        self.prand = float(random_route_prob)
        self.overshoot = bool(overshoot)

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        assignment = self.problem.to_assignment(sol)
        N = len(inst.coords)
        n = N - 1
        if n <= 0 or not assignment:
            free = {next(iter(assignment))} if assignment else set()
            return {k: v for k, v in assignment.items() if k not in free}, free
        k = min(n, max(1, int(round(ratio * n))))
        routes, succ, pred = _routes(assignment, N)
        coords = inst.coords
        cents = []
        for r in routes:
            cx = sum(coords[c][0] for c in r) / len(r)
            cy = sum(coords[c][1] for c in r) / len(r)
            cents.append((cx, cy))
        seed = rng.randrange(len(routes))
        chosen = [seed]
        S = set(routes[seed])
        remaining = [i for i in range(len(routes)) if i != seed]
        sx, sy = cents[seed]
        remaining.sort(key=lambda i: ((cents[i][0] - sx) ** 2 + (cents[i][1] - sy) ** 2, i))
        while len(S) < k and remaining:
            if rng.random() < self.prand:
                idx = rng.randrange(len(remaining))
            else:
                idx = 0
            ri = remaining.pop(idx)
            r = routes[ri]
            if not self.overshoot and len(S) + len(r) > k:
                need = k - len(S)
                start = rng.randrange(len(r) - need + 1)
                S.update(r[start:start + need])
                break
            chosen.append(ri)
            S.update(r)
        free = _free_arcs(S, succ, pred, N, assignment)
        if not free:
            free = {next(iter(assignment))}
        partial = {v: val for v, val in assignment.items() if v not in free}
        return partial, free


def build_component(problem, random_route_prob=0.15, overshoot=True):
    return RouteClusterDestruction(problem, problem.inst, random_route_prob, overshoot)
