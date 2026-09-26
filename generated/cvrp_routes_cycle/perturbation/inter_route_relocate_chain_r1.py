from random import Random
from typing import List, Tuple

COMPONENT = {
    "name": "inter_route_relocate_chain",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class InterRouteRelocateChainPerturbation:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical
        self.inst = problem.inst

    def _as_routes(self, sol) -> List[List[int]]:
        return [list(route) for route in self.canonical(sol)]

    def _from_routes(self, routes: List[List[int]]):
        return self.canonical(tuple(tuple(route) for route in routes))

    def perturb(self, sol, strength: float, rng: Random):
        routes = self._as_routes(sol)
        n_routes = len(routes)
        if not routes:
            return self._from_routes([[]])

        # Prefer larger moves as strength grows.
        max_len = max(1, int(round(strength)))
        source_idx = rng.randrange(n_routes)
        source = routes[source_idx]
        if not source:
            return self._from_routes(routes)

        chain_len = rng.randint(1, min(max_len, len(source)))
        start = rng.randint(0, len(source) - chain_len)
        chain = source[start : start + chain_len]
        remainder = source[:start] + source[start + chain_len :]

        # Choose insertion route (possibly a newly created route).
        dest_choices = list(range(n_routes + 1))  # last index means new route
        dest_idx = rng.choice(dest_choices)

        # Remove source route first, then adjust destination indexing.
        new_routes = []
        for idx, route in enumerate(routes):
            if idx != source_idx:
                new_routes.append(route)
        if remainder:
            if dest_idx > source_idx:
                dest_idx -= 1
            if dest_idx == len(new_routes):
                new_routes.append(remainder)
            else:
                new_routes[dest_idx] = remainder

        if dest_idx == len(new_routes):
            new_routes.append(chain)
        else:
            insert_pos = rng.randint(0, len(new_routes[dest_idx]))
            new_routes[dest_idx] = (
                new_routes[dest_idx][:insert_pos] + chain + new_routes[dest_idx][insert_pos:]
            )

        return self._from_routes(new_routes)


def build_component(problem, **params):
    _ = params.get("strength", 2.0)
    return InterRouteRelocateChainPerturbation(problem)
