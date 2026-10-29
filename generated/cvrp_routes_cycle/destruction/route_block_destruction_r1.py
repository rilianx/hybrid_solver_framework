from random import Random

from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "route_block_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "scope": {"type": "cat", "values": ["internal", "incident"]},
        "random_route_prob": {"type": "float", "range": [0.0, 0.5]},
    },
}


class RouteBlockDestruction:
    """Libera rutas enteras: una ruta semilla y las rutas más próximas a ella
    (distancia mínima cliente-cliente) hasta cubrir ~ratio·n clientes. Con cierta
    probabilidad añade una ruta aleatoria en lugar de la más cercana."""

    def __init__(self, problem, inst, scope="internal", random_route_prob=0.1):
        self.problem = problem
        self.inst = inst
        self.scope = scope
        self.p_rand = float(random_route_prob)

    def _free_arcs(self, nodes):
        n = self.inst.n_customers
        free = set()
        if self.scope == "internal":
            ns = set(nodes) | {0}
            for i in ns:
                for j in ns:
                    if i != j:
                        free.add(f"x_{i}_{j}")
        else:
            for a in nodes:
                for j in range(n + 1):
                    if j != a:
                        free.add(f"x_{a}_{j}")
                        free.add(f"x_{j}_{a}")
        return free

    def _route_dist(self, ra, rb):
        dist = self.inst.dist
        return min(dist(a, b) for a in ra for b in rb)

    def destroy(self, sol, ratio: float, rng: Random):
        routes = list(canonical(sol))
        assignment = self.problem.to_assignment(tuple(routes))
        n = len(list(self.inst.customers))
        if n == 0 or not assignment or not routes:
            free_vars = {rng.choice(sorted(assignment.keys()))} if assignment else set()
            return {v: x for v, x in assignment.items() if v not in free_vars}, free_vars
        k = max(1, min(n, int(round(float(ratio) * n))))
        seed_idx = rng.randrange(len(routes))
        selected = [seed_idx]
        nodes = set(routes[seed_idx])
        remaining = [i for i in range(len(routes)) if i != seed_idx]
        seed_route = routes[seed_idx]
        remaining.sort(key=lambda i: self._route_dist(seed_route, routes[i]))
        while len(nodes) < k and remaining:
            if rng.random() < self.p_rand:
                pos = rng.randrange(len(remaining))
            else:
                pos = 0
            idx = remaining.pop(pos)
            selected.append(idx)
            nodes.update(routes[idx])
        nodes = {c for c in nodes if 1 <= c <= self.inst.n_customers}
        if not nodes:
            nodes = {rng.choice(list(self.inst.customers))}
        free_vars = self._free_arcs(nodes) & set(assignment.keys())
        if not free_vars:
            free_vars = {rng.choice(sorted(assignment.keys()))}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, scope="internal", random_route_prob=0.1):
    return RouteBlockDestruction(problem, problem.inst, scope, random_route_prob)
