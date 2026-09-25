from __future__ import annotations

from math import atan2, pi
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
        depot_x, depot_y = inst.coords[0]

        seed = rng.randrange(1, n + 1)
        sx, sy = inst.coords[seed]
        seed_angle = atan2(sy - depot_y, sx - depot_x)

        def ang_diff(a, b):
            d = abs(a - b) % (2.0 * pi)
            return min(d, 2.0 * pi - d)

        def route_load(route):
            return sum(inst.demand[c] for c in route)

        # Select a route containing customers angularly close to the seed and
        # remove one contiguous block from that route (block relocation, not
        # single-customer relocate).
        best_choice = None
        for ri, r in enumerate(routes):
            if not r:
                continue
            for pos, c in enumerate(r):
                a = atan2(inst.coords[c][1] - depot_y, inst.coords[c][0] - depot_x)
                score = (
                    ang_diff(a, seed_angle),
                    -len(r),  # prefer richer routes for a meaningful block move
                    ri,
                    pos,
                )
                if best_choice is None or score < best_choice[0]:
                    best_choice = (score, ri, pos)

        if best_choice is None:
            return sol

        _, src_ri, src_pos = best_choice
        src_route = routes[src_ri]
        block_len = min(k, len(src_route))
        start = max(0, min(src_pos - block_len // 2, len(src_route) - block_len))
        block = src_route[start : start + block_len]
        if not block:
            return sol

        remaining_routes = []
        removed_set = set(block)
        for ri, r in enumerate(routes):
            if ri == src_ri:
                kept = [c for idx, c in enumerate(r) if not (start <= idx < start + block_len)]
            else:
                kept = [c for c in r if c not in removed_set]
            if kept:
                remaining_routes.append(kept)

        block_demand = sum(inst.demand[c] for c in block)

        def insertion_cost(route, pos, seq):
            prev = 0 if pos == 0 else route[pos - 1]
            nxt = 0 if pos == len(route) else route[pos]
            cost = inst.dist(prev, seq[0]) + inst.dist(seq[-1], nxt) - inst.dist(prev, nxt)
            for i in range(len(seq) - 1):
                cost += inst.dist(seq[i], seq[i + 1])
            return cost

        def feasible_after_inserting(route, seq):
            return route_load(route) + sum(inst.demand[c] for c in seq) <= inst.capacity + 1e-9

        # Repair by best insertion of the whole block; this is a route-fragment
        # move, not a single-customer relocation.
        best = None
        for ri, r in enumerate(remaining_routes):
            if not feasible_after_inserting(r, block):
                continue
            for pos in range(len(r) + 1):
                inc = insertion_cost(r, pos, block)
                key = (inc, ri, pos)
                if best is None or key < best[0]:
                    best = (key, ri, pos)

        if best is None:
            remaining_routes.append(list(block))
        else:
            _, ri, pos = best
            remaining_routes[ri][pos:pos] = block

        # Small extra diversification: if the block came from a long route and
        # there exists another feasible route, try the best insertion there too
        # only when it yields a different canonical structure.
        new_sol = canonical(tuple(tuple(r) for r in remaining_routes))
        if new_sol == sol and len(block) < n:
            alt_routes = [list(r) for r in sol]
            alt_routes[src_ri] = [c for idx, c in enumerate(alt_routes[src_ri]) if not (start <= idx < start + block_len)]
            if alt_routes[src_ri] == []:
                del alt_routes[src_ri]
            alt_routes.append(list(block))
            new_sol = canonical(tuple(tuple(r) for r in alt_routes))

        return new_sol


def build_component(problem, **params):
    return RadialDestroyRepair(problem)
