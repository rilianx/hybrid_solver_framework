from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "segment_relocation_oropt",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {
        "max_seg_len": {"type": "int", "range": [1, 5]},
    },
}


class SegmentRelocationOrOpt:
    """Extrae un segmento consecutivo (largo 1..L) de una ruta y lo inserta, opcionalmente invertido,
    en cualquier posición de la misma ruta, de otra ruta o en una ruta nueva.
    Movimiento = (r_src, start, length, r_dst, pos, rev); r_dst == len(sol) significa ruta nueva."""

    def __init__(self, problem, max_seg_len=3):
        self.problem = problem
        self.L = max(1, int(max_seg_len))
        self._memo_sol = None
        self._memo_val = None

    def _obj(self, sol):
        if self._memo_sol is not None and self._memo_sol == sol:
            return self._memo_val
        v = self.problem.objective(sol)
        self._memo_sol, self._memo_val = sol, v
        return v

    def _valid(self, sol, a, s, l, b, p, rev):
        nr = len(sol)
        if a < 0 or a >= nr:
            return False
        route = sol[a]
        if l < 1 or l > self.L or s < 0 or s + l > len(route):
            return False
        if rev not in (0, 1) or (l == 1 and rev == 1):
            return False
        if b == a:
            if p < 0 or p > len(route) - l:
                return False
            if p == s and rev == 0:
                return False
            return True
        if b == nr:
            return p == 0 and len(route) > l
        if 0 <= b < nr:
            return 0 <= p <= len(sol[b])
        return False

    def moves(self, sol):
        nr = len(sol)
        for a in range(nr):
            route = sol[a]
            n_a = len(route)
            for l in range(1, min(self.L, n_a) + 1):
                for s in range(0, n_a - l + 1):
                    for rev in ((0, 1) if l > 1 else (0,)):
                        for b in range(nr + 1):
                            if b == a:
                                for p in range(0, n_a - l + 1):
                                    if p == s and rev == 0:
                                        continue
                                    yield (a, s, l, b, p, rev)
                            elif b == nr:
                                if n_a > l:
                                    yield (a, s, l, b, 0, rev)
                            else:
                                for p in range(0, len(sol[b]) + 1):
                                    yield (a, s, l, b, p, rev)

    def sample(self, sol, k, rng):
        nr = len(sol)
        out = []
        seen = set()
        if nr == 0:
            return out
        attempts = 0
        while len(out) < k and attempts < 50 * k + 200:
            attempts += 1
            a = rng.randrange(nr)
            n_a = len(sol[a])
            if n_a == 0:
                continue
            l = rng.randint(1, min(self.L, n_a))
            s = rng.randint(0, n_a - l)
            rev = rng.randint(0, 1) if l > 1 else 0
            b = rng.randrange(nr + 1)
            if b == a:
                p = rng.randint(0, n_a - l)
            elif b == nr:
                p = 0
            else:
                p = rng.randint(0, len(sol[b]))
            m = (a, s, l, b, p, rev)
            if m in seen or not self._valid(sol, *m):
                continue
            seen.add(m)
            out.append(m)
        if not out:
            for m in self.moves(sol):
                out.append(m)
                break
        return out

    def apply(self, sol, m):
        a, s, l, b, p, rev = m
        routes = [list(r) for r in sol]
        route = routes[a]
        seg = route[s:s + l]
        if rev:
            seg = seg[::-1]
        rem = route[:s] + route[s + l:]
        if b == a:
            routes[a] = rem[:p] + seg + rem[p:]
        elif b == len(sol):
            routes[a] = rem
            routes.append(seg)
        else:
            routes[a] = rem
            dst = routes[b]
            routes[b] = dst[:p] + seg + dst[p:]
        return canonical(tuple(tuple(r) for r in routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self._obj(sol)


def build_component(problem, max_seg_len=3):
    return SegmentRelocationOrOpt(problem, max_seg_len=max_seg_len)
