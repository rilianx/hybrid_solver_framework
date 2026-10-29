COMPONENT = {
    "name": "or_opt_segment_relocation",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective", "ProblemModel.parts"],
    "params": {
        "max_seg_len": {"type": "int", "range": [1, 3]},
        "allow_new_route": {"type": "bool", "values": [True, False]},
    },
}


class OrOptSegmentRelocation:
    """Movimiento = (r_src, start, length, r_dst, pos, rev).

    Extrae sol[r_src][start:start+length] (invertido si rev=1) y lo inserta en la posición `pos`
    de la ruta r_dst. Si r_dst == r_src, `pos` se mide sobre la ruta ya sin el segmento.
    Si r_dst == len(sol), el segmento forma una ruta nueva.
    """

    def __init__(self, problem, max_seg_len=3, allow_new_route=True):
        self.problem = problem
        self.canon = problem.parts.canonical
        self.max_seg_len = max(1, int(max_seg_len))
        self.allow_new_route = bool(allow_new_route)

    def _valid(self, sol, m):
        ri, s, l, rd, p, rev = m
        nR = len(sol)
        if not (0 <= ri < nR):
            return False
        L = len(sol[ri])
        if l < 1 or l > self.max_seg_len or s < 0 or s + l > L:
            return False
        if rev not in (0, 1) or (rev == 1 and l < 2):
            return False
        rest = L - l
        if rd == nR:
            return self.allow_new_route and rest > 0 and p == 0
        if not (0 <= rd < nR):
            return False
        if rd == ri:
            if not (0 <= p <= rest):
                return False
            if p == s and rev == 0:
                return False
            return True
        return 0 <= p <= len(sol[rd])

    def moves(self, sol):
        nR = len(sol)
        for ri, r in enumerate(sol):
            L = len(r)
            for s in range(L):
                for l in range(1, min(self.max_seg_len, L - s) + 1):
                    rest = L - l
                    for rev in ((0, 1) if l >= 2 else (0,)):
                        for rd in range(nR):
                            if rd == ri:
                                for p in range(rest + 1):
                                    if p == s and rev == 0:
                                        continue
                                    yield (ri, s, l, rd, p, rev)
                            else:
                                for p in range(len(sol[rd]) + 1):
                                    yield (ri, s, l, rd, p, rev)
                        if self.allow_new_route and rest > 0:
                            yield (ri, s, l, nR, 0, rev)

    def sample(self, sol, k, rng):
        out = []
        seen = set()
        nR = len(sol)
        if nR == 0:
            return out
        attempts = 0
        while len(out) < k and attempts < 30 * k + 50:
            attempts += 1
            ri = rng.randrange(nR)
            L = len(sol[ri])
            s = rng.randrange(L)
            l = rng.randint(1, min(self.max_seg_len, L - s))
            rev = rng.randint(0, 1) if l >= 2 else 0
            rest = L - l
            top = nR + (1 if (self.allow_new_route and rest > 0) else 0)
            rd = rng.randrange(top)
            if rd == nR:
                p = 0
            elif rd == ri:
                p = rng.randint(0, rest)
            else:
                p = rng.randint(0, len(sol[rd]))
            m = (ri, s, l, rd, p, rev)
            if m in seen or not self._valid(sol, m):
                continue
            seen.add(m)
            out.append(m)
        return out

    def apply(self, sol, m):
        ri, s, l, rd, p, rev = m
        routes = [list(r) for r in sol]
        seg = routes[ri][s:s + l]
        if rev:
            seg.reverse()
        del routes[ri][s:s + l]
        if rd == len(sol):
            routes.append(seg)
        else:
            tgt = routes[rd]
            routes[rd] = tgt[:p] + seg + tgt[p:]
        return self.canon(routes)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_seg_len=3, allow_new_route=True):
    return OrOptSegmentRelocation(problem, max_seg_len=max_seg_len, allow_new_route=allow_new_route)
