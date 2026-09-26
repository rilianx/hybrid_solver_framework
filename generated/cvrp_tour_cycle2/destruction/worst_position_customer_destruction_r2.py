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
    """Libera un bloque contiguo del gran tour centrado en posiciones de peor contribución local."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _extract_tour_order(self, assignment: dict[str, float]) -> list[int]:
        succ: dict[int, int] = {}
        pred: dict[int, int] = {}
        nodes: set[int] = set()

        for var, val in assignment.items():
            if not var.startswith("x_") or val <= 0.5:
                continue
            parts = var.split("_")
            if len(parts) != 3:
                continue
            _, i, j = parts
            ii, jj = int(i), int(j)
            if ii == jj:
                continue
            succ[ii] = jj
            pred[jj] = ii
            nodes.add(ii)
            nodes.add(jj)

        starts = [n for n in nodes if n != 0 and n not in pred]
        if 0 in succ:
            start = succ[0]
        elif starts:
            start = starts[0]
        else:
            return []

        order: list[int] = []
        cur = start
        seen: set[int] = set()
        while cur != 0 and cur not in seen:
            order.append(cur)
            seen.add(cur)
            cur = succ.get(cur, 0)
        return order

    def _position_scores(self, tour: list[int]) -> list[tuple[float, int]]:
        scored: list[tuple[float, int]] = []
        n = len(tour)
        if n == 0:
            return scored
        for idx, c in enumerate(tour):
            prev_node = 0 if idx == 0 else tour[idx - 1]
            next_node = 0 if idx == n - 1 else tour[idx + 1]
            gain = self.inst.dist(prev_node, c) + self.inst.dist(c, next_node) - self.inst.dist(prev_node, next_node)
            scored.append((gain, idx))
        scored.sort(reverse=True)
        return scored

    def _choose_block(self, tour: list[int], ratio: float, rng: Random) -> tuple[int, int]:
        n = len(tour)
        if n == 0:
            return 0, 0
        k = max(1, int(round(ratio * n)))
        k = min(k, n)

        scored = self._position_scores(tour)
        if not scored:
            start = rng.randrange(n)
            return start, min(n, start + k)

        best_idx = scored[0][1]
        half = k // 2
        start = max(0, best_idx - half)
        end = start + k
        if end > n:
            end = n
            start = max(0, end - k)

        return start, end

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        tour = self._extract_tour_order(assignment)

        if not tour:
            free_vars = set()
            for var in assignment:
                if var.startswith("x_"):
                    free_vars.add(var)
                    break
            if not free_vars:
                return dict(assignment), set()
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        start, end = self._choose_block(tour, ratio, rng)
        selected = set(tour[start:end])

        free_vars: set[str] = set()
        for var in assignment:
            if not var.startswith("x_"):
                continue
            parts = var.split("_")
            if len(parts) != 3:
                continue
            _, i, j = parts
            ii, jj = int(i), int(j)
            if ii in selected or jj in selected:
                free_vars.add(var)

        if not free_vars:
            for var in assignment:
                if var.startswith("x_"):
                    free_vars.add(var)
                    break

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = float(params.get("ratio", 0.2))
    return WorstPositionCustomerDestruction(problem, problem.inst)
