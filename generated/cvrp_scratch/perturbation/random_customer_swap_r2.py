from __future__ import annotations

from random import Random

from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "random_customer_swap",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class RandomCustomerSwap:
    def perturb(self, sol, strength: float, rng: Random):
        routes = [list(r) for r in sol]
        if not routes:
            return sol

        attempts = max(1, int(round(strength)))

        def canon(curr_routes):
            return canonical(tuple(tuple(r) for r in curr_routes))

        new_sol = sol

        # Try elementary customer swaps first.
        for _ in range(attempts):
            nonempty = [i for i, r in enumerate(routes) if r]
            if len(nonempty) < 1:
                break
            if len(nonempty) == 1 and len(routes[nonempty[0]]) < 2:
                break

            r1 = rng.choice(nonempty)
            c1_pos = rng.randrange(len(routes[r1]))
            c1 = routes[r1][c1_pos]

            r2 = rng.choice(nonempty)
            c2_pos = rng.randrange(len(routes[r2]))
            c2 = routes[r2][c2_pos]

            if r1 == r2 and c1_pos == c2_pos:
                if len(routes[r1]) < 2:
                    continue
                c2_pos = (c1_pos + 1) % len(routes[r1])
                c2 = routes[r1][c2_pos]

            routes[r1][c1_pos], routes[r2][c2_pos] = c2, c1
            new_sol = canon(routes)
            if new_sol != sol:
                return new_sol

        # Fallback: a single customer relocate, still elementary, to avoid no-op
        # in cases where swapping singleton routes is canonical-equivalent.
        routes = [list(r) for r in sol]
        movable_sources = [i for i, r in enumerate(routes) if len(r) >= 1]
        if len(movable_sources) < 1:
            return sol

        src = rng.choice(movable_sources)
        pos = rng.randrange(len(routes[src]))
        customer = routes[src].pop(pos)

        target_routes = [i for i in range(len(routes)) if i != src]
        if target_routes:
            dst = rng.choice(target_routes)
            insert_pos = rng.randrange(len(routes[dst]) + 1)
            routes[dst].insert(insert_pos, customer)
        else:
            # Single route instance: relocate inside the same route.
            if len(routes[src]) == 0:
                routes[src].append(customer)
            else:
                insert_pos = rng.randrange(len(routes[src]) + 1)
                routes[src].insert(insert_pos, customer)

        new_sol = canon(routes)
        return new_sol if new_sol != sol else sol


def build_component(problem, **params):
    return RandomCustomerSwap()
