from random import Random

COMPONENT = {
    "name": "worst_detour_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "determinism": {"type": "float", "range": [1.0, 10.0]},
        "normalize": {"type": "bool", "values": [True, False]},
    },
}


def _xn(i, j):
    return f"x_{i}_{j}"


def _links(assignment, N):
    succ, pred = {}, {}
    for i in range(N):
        for j in range(N):
            if i != j and assignment.get(_xn(i, j), 0.0) > 0.5:
                if i != 0:
                    succ.setdefault(i, j)
                if j != 0:
                    pred.setdefault(j, i)
    return succ, pred


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


class WorstDetourDestruction:
    """Libera los clientes con mayor ahorro por eliminación, recalculando tras cada extracción."""

    def __init__(self, problem, inst, determinism, normalize):
        self.problem, self.inst = problem, inst
        self.p = float(determinism)
        self.normalize = bool(normalize)

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        assignment = self.problem.to_assignment(sol)
        N = len(inst.coords)
        n = N - 1
        if n <= 0 or not assignment:
            free = {next(iter(assignment))} if assignment else set()
            return {k: v for k, v in assignment.items() if k not in free}, free
        k = min(n, max(1, int(round(ratio * n))))
        succ, pred = _links(assignment, N)
        dist = inst.dist
        # copia de trabajo de los enlaces para recalcular desvíos tras cada extracción
        s_cur = {c: succ.get(c, 0) for c in range(1, N)}
        p_cur = {c: pred.get(c, 0) for c in range(1, N)}
        alive = set(range(1, N))
        S = set()
        while len(S) < k and alive:
            def gain(c):
                a, b = p_cur[c], s_cur[c]
                g = dist(a, c) + dist(c, b) - dist(a, b)
                if self.normalize:
                    g /= max(1e-9, dist(0, c))
                return g
            cand = sorted(alive, key=lambda c: (-gain(c), c))
            idx = int((rng.random() ** self.p) * len(cand))
            c = cand[min(idx, len(cand) - 1)]
            S.add(c)
            alive.discard(c)
            a, b = p_cur[c], s_cur[c]
            if a != 0:
                s_cur[a] = b
            if b != 0:
                p_cur[b] = a
        free = _free_arcs(S, succ, pred, N, assignment)
        if not free:
            free = {next(iter(assignment))}
        partial = {v: val for v, val in assignment.items() if v not in free}
        return partial, free


def build_component(problem, determinism=3.0, normalize=False):
    return WorstDetourDestruction(problem, problem.inst, determinism, normalize)
