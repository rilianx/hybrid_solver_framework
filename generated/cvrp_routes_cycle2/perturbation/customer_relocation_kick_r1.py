from random import Random

COMPONENT = {
    "name": "customer_relocation_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 50.0]},
    },
}


class CustomerRelocationKick:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical
        self.inst = problem.inst

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.canonical(sol)
        routes = [list(route) for route in sol]
        customers = [c for route in routes for c in route]
        if len(customers) <= 1:
            return sol

        steps = max(1, int(round(strength)))
        for _ in range(steps):
            nonempty = [i for i, r in enumerate(routes) if r]
            if not nonempty:
                break

            r_idx = rng.choice(nonempty)
            route = routes[r_idx]
            if not route:
                continue

            pos = rng.randrange(len(route))
            c = route.pop(pos)

            if not route:
                del routes[r_idx]
            insert_positions = []
            for i in range(len(routes) + 1):
                insert_positions.append(i)
            t_idx = rng.choice(insert_positions)

            if t_idx == len(routes):
                routes.append([c])
            else:
                target = routes[t_idx]
                ipos = rng.randrange(len(target) + 1)
                target.insert(ipos, c)

        if not routes:
            return sol

        new_sol = self.canonical(tuple(tuple(r) for r in routes))
        if new_sol == sol:
            # Fallback deterministic move to ensure a distinct solution
            routes = [list(route) for route in sol]
            for i, route in enumerate(routes):
                if route:
                    c = route.pop()
                    if not route:
                        del routes[i]
                    if routes:
                        routes[0].insert(0, c)
                    else:
                        routes = [[c]]
                    break
            new_sol = self.canonical(tuple(tuple(r) for r in routes))
        return new_sol


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return CustomerRelocationKick(problem)
