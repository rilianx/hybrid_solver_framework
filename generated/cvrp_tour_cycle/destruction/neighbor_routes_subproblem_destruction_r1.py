from random import Random

from generated.cvrp_tour_cycle.model.parts import canonical  # noqa: F401

COMPONENT = {
    "name": "neighbor_routes_subproblem_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "min_routes": {"type": "int", "range": [1, 4]},
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
    return routes


class NeighborRoutesSubproblemDestruction:
    """Elige una ruta semilla al azar y agrega las rutas más próximas (distancia mínima entre
    clientes) hasta cubrir ratio·n clientes; libera todos los arcos entre esos clientes y el
    depósito, de modo que el sub-MIP re-resuelve un CVRP cerrado sobre esas rutas."""

    def __init__(self, problem, inst, min_routes):
        self.problem, self.inst = problem, inst
        self.min_routes = min_routes

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        assignment = self.problem.to_assignment(sol)
        customers = list(inst.customers)
        n = len(customers)
        nn = inst.n_customers
        if n == 0:
            return {}, set()
        k = max(1, min(n, int(round(max(0.0, ratio) * n))))
        routes = _parse_routes(assignment)
        covered = {c for r in routes for c in r}
        for c in customers:
            if c not in covered:
                routes.append([c])

        seed = rng.randrange(len(routes))
        seed_route = routes[seed]

        def route_gap(r):
            return min(inst.dist(a, b) for a in seed_route for b in r)

        others = [i for i in range(len(routes)) if i != seed]
        jitter = {i: rng.random() * 1e-9 for i in others}
        others.sort(key=lambda i: route_gap(routes[i]) + jitter[i])

        chosen = [seed]
        S = set(seed_route)
        for i in others:
            if len(S) >= k and len(chosen) >= self.min_routes:
                break
            chosen.append(i)
            S.update(routes[i])

        A = S | {0}
        free_vars = set()
        for i in A:
            for j in A:
                if i != j:
                    name = f"x_{i}_{j}"
                    if name in assignment:
                        free_vars.add(name)
        if not free_vars:
            free_vars.add(next(iter(assignment)))
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, min_routes=2):
    return NeighborRoutesSubproblemDestruction(problem, problem.inst, min_routes)
