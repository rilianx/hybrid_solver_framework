from generated.cvrp_tour_cycle.model.parts import canonical, _split_dp

COMPONENT = {
    "name": "decoded_routes_2opt_star_tail_exchange",
    "slot": "neighborhood",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'MIP_PERTURB'],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class DecodedRoutes2OptStar:
    """Decodifica rutas con Split. Movimiento = (0, a, p1, b, p2) con a < b:
    ra' = ra[:p1] + rb[p2:], rb' = rb[:p2] + ra[p1:]; se concatenan las rutas en su orden.
    Si hay una sola ruta: movimiento = (1, i, j), que invierte el tramo [i, j] de esa ruta."""

    def __init__(self, problem):
        self.problem = problem
        self._c_sol = None
        self._c_obj = None
        self._r_sol = None
        self._r_routes = None

    def _obj(self, sol):
        if self._c_sol is not None and self._c_sol == sol:
            return self._c_obj
        v = self.problem.objective(sol)
        self._c_sol = sol
        self._c_obj = v
        return v

    def _routes(self, sol):
        if self._r_sol is not None and self._r_sol == sol:
            return self._r_routes
        routes, _ = _split_dp(self.problem.inst, tuple(sol))
        routes = [tuple(r) for r in routes if len(r) > 0]
        self._r_sol = sol
        self._r_routes = routes
        return routes

    @staticmethod
    def _valid_tail(la, lb, p1, p2):
        if p1 < 0 or p1 > la or p2 < 0 or p2 > lb:
            return False
        if p1 == 0 and p2 == 0:
            return False
        if p1 == la and p2 == lb:
            return False
        return True

    def moves(self, sol):
        sol = canonical(sol)
        routes = self._routes(sol)
        R = len(routes)
        out = []
        if R >= 2:
            for a in range(R - 1):
                la = len(routes[a])
                for b in range(a + 1, R):
                    lb = len(routes[b])
                    for p1 in range(la + 1):
                        for p2 in range(lb + 1):
                            if self._valid_tail(la, lb, p1, p2):
                                out.append((0, a, p1, b, p2))
        if not out:
            n = len(sol)
            for i in range(n - 1):
                for j in range(i + 1, n):
                    out.append((1, i, j))
        return out

    def sample(self, sol, k, rng):
        sol = canonical(sol)
        routes = self._routes(sol)
        R = len(routes)
        if R < 2:
            full = self.moves(sol)
            return rng.sample(full, min(k, len(full)))
        res = []
        seen = set()
        attempts = 0
        while len(res) < k and attempts < 30 * max(1, k):
            attempts += 1
            a, b = sorted(rng.sample(range(R), 2))
            la, lb = len(routes[a]), len(routes[b])
            p1 = rng.randint(0, la)
            p2 = rng.randint(0, lb)
            if not self._valid_tail(la, lb, p1, p2):
                continue
            m = (0, a, p1, b, p2)
            if m in seen:
                continue
            seen.add(m)
            res.append(m)
        if not res:
            full = self.moves(sol)
            res = rng.sample(full, min(k, len(full)))
        return res

    def apply(self, sol, m):
        sol = canonical(sol)
        if m[0] == 1:
            _, i, j = m
            return canonical(sol[:i] + tuple(reversed(sol[i:j + 1])) + sol[j + 1:])
        _, a, p1, b, p2 = m
        routes = list(self._routes(sol))
        ra, rb = routes[a], routes[b]
        routes[a] = ra[:p1] + rb[p2:]
        routes[b] = rb[:p2] + ra[p1:]
        tour = []
        for r in routes:
            tour.extend(r)
        return canonical(tuple(tour))

    def delta(self, sol, m):
        sol = canonical(sol)
        return self.problem.objective(self.apply(sol, m)) - self._obj(sol)


def build_component(problem):
    return DecodedRoutes2OptStar(problem)
