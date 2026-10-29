from generated.cvrp_tour_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "granular_segment_relocate",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {
        "k_neighbors": {"type": "int", "range": [3, 30]},
        "max_len": {"type": "int", "range": [1, 4]},
    },
}


class GranularSegmentRelocate:
    """Toma el segmento del gran tour que empieza en el cliente c (largo L) y lo reinserta
    adyacente a uno de los k vecinos más cercanos v de c: detrás de v (v,c,...) o, invertido,
    delante de v (...,c,v). Movimiento = (c, L, v, side)."""

    def __init__(self, problem, k_neighbors=10, max_len=3):
        self.problem = problem
        inst = problem.inst
        self.n = inst.n_customers
        self.max_len = max(1, int(max_len))
        k = max(1, int(k_neighbors))
        self.neigh = {}
        for c in range(1, self.n + 1):
            others = [v for v in range(1, self.n + 1) if v != c]
            others.sort(key=lambda v: (inst.dist(c, v), v))
            self.neigh[c] = others[:k]

    def _all_moves(self, sol):
        sol = canonical(sol)
        m = len(sol)
        out = []
        for p, c in enumerate(sol):
            for L in range(1, self.max_len + 1):
                if p + L > m:
                    break
                seg = set(sol[p:p + L])
                for v in self.neigh.get(c, []):
                    if v in seg:
                        continue
                    out.append((c, L, v, 0))
                    out.append((c, L, v, 1))
        if not out and m >= 1:
            out.append((sol[0], 1, sol[0], 0))  # no-op de respaldo
        return out

    def moves(self, sol):
        return iter(self._all_moves(sol))

    def sample(self, sol, k, rng):
        allm = self._all_moves(sol)
        k = min(int(k), len(allm))
        return rng.sample(allm, k)

    def apply(self, sol, m):
        c, L, v, side = m
        s = list(canonical(sol))
        if c not in s or v not in s:
            return canonical(s)
        p = s.index(c)
        if p + L > len(s):
            return canonical(s)
        seg = s[p:p + L]
        if v in seg:
            return canonical(s)
        rest = s[:p] + s[p + L:]
        q = rest.index(v)
        if side == 0:
            new = rest[:q + 1] + seg + rest[q + 1:]
        else:
            new = rest[:q] + seg[::-1] + rest[q:]
        return canonical(new)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, k_neighbors=10, max_len=3):
    return GranularSegmentRelocate(problem, k_neighbors=k_neighbors, max_len=max_len)
