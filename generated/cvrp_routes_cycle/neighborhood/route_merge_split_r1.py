from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "route_merge_split",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {
        "split_only_overloaded": {"type": "bool"},
    },
}


class RouteMergeSplit:
    """Opera sobre rutas enteras:
    ("merge", a, b, oa, ob): reemplaza A y B por una sola ruta (A u rev A) + (B u rev B),
        solo si la carga conjunta cabe en la capacidad (estilo ahorros de Clarke-Wright, 4 orientaciones).
    ("split", r, p, o): parte la ruta r en route[:p] y route[p:] (o=1 invierte la segunda parte);
        si split_only_overloaded, solo se ofrecen cortes de rutas sobrecargadas (reparación).
    ("noop",) solo si no existe ningún otro movimiento."""

    def __init__(self, problem, split_only_overloaded=True):
        self.problem = problem
        self.inst = problem.inst
        self.split_only_overloaded = bool(split_only_overloaded)
        self._memo_sol = None
        self._memo_val = None

    def _obj(self, sol):
        if self._memo_sol is not None and self._memo_sol == sol:
            return self._memo_val
        v = self.problem.objective(sol)
        self._memo_sol, self._memo_val = sol, v
        return v

    def _load(self, route):
        n = self.inst.n_customers
        return sum(self.inst.demand[c] for c in route if 1 <= c <= n)

    def _split_routes(self, sol):
        cap = self.inst.capacity
        res = []
        for r, route in enumerate(sol):
            if len(route) >= 2 and (not self.split_only_overloaded or self._load(route) > cap):
                res.append(r)
        return res

    def _merge_pairs(self, sol):
        cap = self.inst.capacity
        loads = [self._load(r) for r in sol]
        pairs = []
        for a in range(len(sol)):
            for b in range(a + 1, len(sol)):
                if loads[a] + loads[b] <= cap:
                    pairs.append((a, b))
        return pairs

    def moves(self, sol):
        found = False
        for a, b in self._merge_pairs(sol):
            for oa in (0, 1):
                for ob in (0, 1):
                    found = True
                    yield ("merge", a, b, oa, ob)
        for r in self._split_routes(sol):
            for p in range(1, len(sol[r])):
                for o in (0, 1):
                    found = True
                    yield ("split", r, p, o)
        if not found:
            yield ("noop",)

    def sample(self, sol, k, rng):
        pairs = self._merge_pairs(sol)
        splits = self._split_routes(sol)
        if not pairs and not splits:
            return [("noop",)]
        out, seen = [], set()
        attempts = 0
        while len(out) < k and attempts < 50 * k + 200:
            attempts += 1
            if pairs and (not splits or rng.random() < 0.5):
                a, b = rng.choice(pairs)
                m = ("merge", a, b, rng.randint(0, 1), rng.randint(0, 1))
            else:
                r = rng.choice(splits)
                m = ("split", r, rng.randint(1, len(sol[r]) - 1), rng.randint(0, 1))
            if m in seen:
                continue
            seen.add(m)
            out.append(m)
        return out

    def apply(self, sol, m):
        if m[0] == "noop":
            return canonical(sol)
        routes = [tuple(r) for r in sol]
        if m[0] == "merge":
            _, a, b, oa, ob = m
            A = routes[a][::-1] if oa else routes[a]
            B = routes[b][::-1] if ob else routes[b]
            new = A + B
            rest = [routes[i] for i in range(len(routes)) if i != a and i != b]
            rest.append(new)
            return canonical(tuple(rest))
        _, r, p, o = m
        route = routes[r]
        first, second = route[:p], route[p:]
        if o:
            second = second[::-1]
        routes[r] = first
        routes.append(second)
        return canonical(tuple(routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self._obj(sol)


def build_component(problem, split_only_overloaded=True):
    return RouteMergeSplit(problem, split_only_overloaded=split_only_overloaded)
