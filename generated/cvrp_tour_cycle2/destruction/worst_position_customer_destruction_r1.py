from random import Random
from typing import Any

COMPONENT = {
    "name": "worst_position_customer_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class WorstPositionCustomerDestruction:
    """Libera clientes con peor contribución local estimada en el tour decodificado."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _extract_routes(self, assignment: dict[str, float]) -> list[list[int]]:
        succ: dict[int, int] = {}
        starts: list[int] = []
        for var, val in assignment.items():
            if not var.startswith("x_") or val <= 0.5:
                continue
            _, i, j = var.split("_")
            ii, jj = int(i), int(j)
            succ[ii] = jj
            if ii == 0 and jj != 0:
                starts.append(jj)

        routes: list[list[int]] = []
        used: set[int] = set()
        for s in starts:
            if s in used:
                continue
            route: list[int] = []
            cur = s
            while cur != 0 and cur not in used:
                route.append(cur)
                used.add(cur)
                cur = succ.get(cur, 0)
            if route:
                routes.append(route)

        for c in self.inst.customers:
            if c not in used:
                routes.append([c])
        return routes

    def _score_customers(self, assignment: dict[str, float]) -> list[tuple[float, int]]:
        routes = self._extract_routes(assignment)
        scored: list[tuple[float, int]] = []
        for route in routes:
            for idx, c in enumerate(route):
                prev_node = 0 if idx == 0 else route[idx - 1]
                next_node = 0 if idx == len(route) - 1 else route[idx + 1]
                base = self.inst.dist(prev_node, c) + self.inst.dist(c, next_node)
                gain = base - self.inst.dist(prev_node, next_node)
                scored.append((gain, c))
        scored.sort(reverse=True)
        return scored

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        scored = self._score_customers(assignment)
        if not scored:
            free_vars = {next(v for v in assignment if v.startswith("x_"))}
            return {v: val for v, val in assignment.items() if v not in free_vars}, free_vars

        k = max(1, int(round(ratio * len(self.inst.customers))))
        k = min(k, len(self.inst.customers), len(scored))
        chosen = {c for _, c in scored[:k]}

        free_vars: set[str] = set()
        for var in assignment:
            if not var.startswith("x_"):
                continue
            _, i, j = var.split("_")
            ii, jj = int(i), int(j)
            if ii in chosen or jj in chosen:
                free_vars.add(var)

        if not free_vars:
            # Ensure at least one variable is freed.
            for var in assignment:
                if var.startswith("x_"):
                    free_vars.add(var)
                    break

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = float(params.get("ratio", 0.2))
    return WorstPositionCustomerDestruction(problem, problem.inst)
