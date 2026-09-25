from __future__ import annotations

from random import Random

from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "radial_destroy_repair",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class RadialDestroyRepair:
    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        routes = [list(r) for r in sol]
        n = inst.n_customers
        if n == 0:
            return sol

        k = max(1, min(n, int(round(strength))))
        depot = inst.coords[0]

        # 1) choose a seed customer and destroy a radial neighborhood around it
        seed = rng.randrange(1, n + 1)
        sx, sy = inst.coords[seed]
        target = sorted(
            range(1, n + 1),
            key=lambda c: ((inst.coords[c][0] - sx) ** 2 + (inst.coords[c][1] - sy) ** 2, c),
        )
        removed = set(target[:k])

        kept_routes = []
        removed_list = []
        for r in routes:
            kept = [c for c in r if c not in removed]
            if kept:
                kept_routes.append(kept)
            for c in r:
                if c in removed:
                    removed_list.append(c)

        # 2) greedily reinsert removed customers where they fit best by distance increase
        def route_load(route):
            return sum(inst.demand[c] for c in route)

        for c in removed_list:
            best = None
            best_inc = None
            for ri, r in enumerate(kept_routes):
                if route_load(r) + inst.demand[c] > inst.capacity + 1e-9:
                    continue
                prev = 0
                for pos in range(len(r) + 1):
                    nxt = r[pos] if pos < len(r) else 0
                    inc = inst.dist(prev, c) + inst.dist(c, nxt) - inst.dist(prev, nxt)
                    if best_inc is None or inc < best_inc - 1e-12:
                        best_inc = inc
                        best = (ri, pos)
                    prev = nxt
            if best is None:
                kept_routes.append([c])
            else:
                ri, pos = best
                kept_routes[ri].insert(pos, c)

        new_sol = canonical(tuple(tuple(r) for r in kept_routes))
        if new_sol == sol:
            # fallback: force a nontrivial radial move
            if len(sol) >= 1 and sol[0]:
                c = sol[0][0]
                others = [list(r) for r in sol]
                others[0] = others[0][1:]
                others.append([c])
                new_sol = canonical(tuple(tuple(r) for r in others))
        return new_sol


def build_component(problem, **params):
    return RadialDestroyRepair(problem)
