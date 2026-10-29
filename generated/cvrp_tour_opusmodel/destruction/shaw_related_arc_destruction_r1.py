from random import Random

COMPONENT = {
    "name": "shaw_related_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "determinism": {"type": "float", "range": [1.0, 10.0]},
        "demand_weight": {"type": "float", "range": [0.0, 1.0]},
        "route_weight": {"type": "float", "range": [0.0, 1.0]},
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
    return routes, succ, pred


def _free_arcs(S, succ, pred, N, assignment):
    A = {0}
    for c in S:
        A.add(c)
        A.add(succ.get(c, 0))
        A.add(pred.get(c, 0))
    free = set()
    for c in S:
        for i in range(N):
            if i != c:
                free.add(_xn(i, c))
                free.add(_xn(c, i))
    for a in A:
        for b in A:
            if a != b:
                free.add(_xn(a, b))
    return {v for v in free if v in assignment}


class ShawRelatedArcDestruction:
    """Selección iterativa de clientes relacionados (Shaw) y liberación de sus arcos."""

    def __init__(self, problem, inst, determinism, demand_weight, route_weight):
        self.problem, self.inst = problem, inst
        self.p = float(determinism)
        self.wd = float(demand_weight)
        self.wr = float(route_weight)

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        assignment = self.problem.to_assignment(sol)
        N = len(inst.coords)
        n = N - 1
        if n <= 0 or not assignment:
            v = next(iter(assignment)) if assignment else None
            free = {v} if v is not None else set()
            return {k: val for k, val in assignment.items() if k not in free}, free
        k = min(n, max(1, int(round(ratio * n))))
        routes, succ, pred = _routes(assignment, N)
        rid = {}
        for idx, r in enumerate(routes):
            for c in r:
                rid[c] = idx
        dist = inst.dist
        dem = inst.demand
        maxd = max(1e-9, max(dist(i, j) for i in range(1, N) for j in range(1, N)) if n > 1 else 1.0)
        maxq = max(1e-9, max(dem[c] for c in range(1, N)))

        def rel(a, b):
            r = dist(a, b) / maxd + self.wd * abs(dem[a] - dem[b]) / maxq
            if rid.get(a, -1) != rid.get(b, -2):
                r += self.wr
            return r

        seed = rng.randint(1, n)
        removed = [seed]
        rem_set = {seed}
        while len(removed) < k:
            ref = rng.choice(removed)
            cand = sorted((c for c in range(1, N) if c not in rem_set), key=lambda c: (rel(ref, c), c))
            if not cand:
                break
            idx = int((rng.random() ** self.p) * len(cand))
            c = cand[min(idx, len(cand) - 1)]
            removed.append(c)
            rem_set.add(c)
        free = _free_arcs(rem_set, succ, pred, N, assignment)
        if not free:
            free = {next(iter(assignment))}
        partial = {v: val for v, val in assignment.items() if v not in free}
        return partial, free


def build_component(problem, determinism=4.0, demand_weight=0.3, route_weight=0.2):
    return ShawRelatedArcDestruction(problem, problem.inst, determinism, demand_weight, route_weight)
