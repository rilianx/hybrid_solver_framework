import re
from random import Random
COMPONENT = {
    "name": "worst_detour_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "determinism": {"type": "float", "range": [1.0, 10.0]},
        "normalize": {"type": "bool", "values": [True, False]},
        "neighbors": {"type": "int", "range": [2, 12]},
    },
}


_ARC_RE = re.compile(r"(\d+)\D+(\d+)\D*$")


def _local_free_arcs(S, succ, pred, near, assignment):
    """Libera solo arcos locales: cliente <-> sus vecinos cercanos, depósito y enlaces actuales,
    más los arcos entre los extremos que quedan expuestos (para poder reconectar)."""
    index = _arc_index(assignment)
    A = {0}
    free = set()

    def add(i, j):
        v = index.get((i, j))
        if v is not None:
            free.add(v)

    for c in S:
        p, s = pred.get(c, 0), succ.get(c, 0)
        A.add(c)
        A.add(p)
        A.add(s)
        targets = set(near.get(c, ())) | {0, p, s}
        for j in targets:
            if j != c:
                add(c, j)
                add(j, c)
    for a in A:
        for b in A:
            if a != b:
                add(a, b)
    return free


class WorstDetourDestruction:
    def __init__(self, problem, inst, determinism, normalize, neighbors=4):
        self.problem, self.inst = problem, inst
        self.p = float(determinism)
        self.normalize = bool(normalize)
        self.K = max(1, int(neighbors))
        self._near = None

    def _neighbors(self, N):
        if self._near is None or len(self._near) != N - 1:
            dist = self.inst.dist
            near = {}
            for c in range(1, N):
                others = sorted((j for j in range(1, N) if j != c), key=lambda j: (dist(c, j), j))
                near[c] = others[: self.K]
            self._near = near
        return self._near

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
        s_cur = {c: succ.get(c, 0) for c in range(1, N)}
        p_cur = {c: pred.get(c, 0) for c in range(1, N)}
        alive = set(range(1, N))
        S = set()
        normalize = self.normalize

        def gain(c):
            a, b = p_cur[c], s_cur[c]
            g = dist(a, c) + dist(c, b) - dist(a, b)
            if normalize:
                g /= max(1e-9, dist(0, c))
            return g

        while len(S) < k and alive:
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
        near = self._neighbors(N)
        free = _local_free_arcs(S, succ, pred, near, assignment)
        if not free:
            free = {next(iter(assignment))}
        partial = {v: val for v, val in assignment.items() if v not in free}
        return partial, free


def build_component(problem, determinism=3.0, normalize=False, neighbors=4):
    return WorstDetourDestruction(problem, problem.inst, determinism, normalize, neighbors)


def _parse_arc(name):
    """Extrae (i, j) de un nombre de variable de arco (últimos dos enteros del nombre)."""
    if isinstance(name, tuple):
        nums = [t for t in name if isinstance(t, int)]
        if len(nums) >= 2:
            return nums[-2], nums[-1]
        return None
    m = _ARC_RE.search(str(name))
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _arc_index(assignment):
    idx = {}
    for v in assignment:
        ij = _parse_arc(v)
        if ij is not None:
            idx[ij] = v
    return idx


def _links(assignment, N):
    """Sucesor/predecesor de cada cliente según los arcos activos de la asignación."""
    succ, pred = {}, {}
    for v, val in assignment.items():
        try:
            active = float(val) > 0.5
        except (TypeError, ValueError):
            active = bool(val)
        if not active:
            continue
        ij = _parse_arc(v)
        if ij is None:
            continue
        i, j = ij
        if i == j or not (0 <= i < N and 0 <= j < N):
            continue
        if i != 0:
            succ[i] = j
        if j != 0:
            pred[j] = i
    return succ, pred
