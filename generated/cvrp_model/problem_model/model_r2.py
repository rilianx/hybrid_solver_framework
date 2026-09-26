from __future__ import annotations

from itertools import combinations
from math import inf
from typing import Any

import pulp


COMPONENT = {
    "name": "cvrp_mip_view_fixed",
    "slot": "problem_model",
    "compatible_skeletons": ["generic_hybrid", "matheuristic_hybrid"],
    "requires": [],
    "params": {},
}


def _nodes(inst):
    return range(inst.n_customers + 1)


def _customers(inst):
    return range(1, inst.n_customers + 1)


def _route_distance(inst, route: tuple[int, ...]) -> float:
    if not route:
        return 0.0
    d = inst.dist(0, route[0]) + inst.dist(route[-1], 0)
    for i in range(len(route) - 1):
        d += inst.dist(route[i], route[i + 1])
    return d


def _normalize_solution(sol):
    if isinstance(sol, tuple):
        return sol
    return tuple(tuple(r) for r in sol)


class ProblemModel:
    def __init__(self, inst):
        self.inst = inst

    def objective(self, sol) -> float:
        sol = _normalize_solution(sol)
        seen = set()
        dist = 0.0
        penalty = 0.0
        for route in sol:
            if not isinstance(route, tuple) or len(route) == 0:
                penalty += 1_000_000.0
                continue
            prev = 0
            load = 0.0
            for c in route:
                if c == 0 or c > self.inst.n_customers or c in seen:
                    penalty += 1_000_000.0
                else:
                    seen.add(c)
                load += self.inst.demand[c]
                dist += self.inst.dist(prev, c)
                prev = c
            dist += self.inst.dist(prev, 0)
            if load > self.inst.capacity + 1e-9:
                penalty += 10_000.0 * (load - self.inst.capacity)
        missing = self.inst.n_customers - len(seen)
        if missing > 0:
            penalty += 1_000_000.0 * missing
        return dist + penalty

    def is_feasible(self, sol) -> bool:
        sol = _normalize_solution(sol)
        seen = set()
        for route in sol:
            if not isinstance(route, tuple) or len(route) == 0:
                return False
            load = 0.0
            for c in route:
                if c == 0 or c > self.inst.n_customers or c in seen:
                    return False
                seen.add(c)
                load += self.inst.demand[c]
            if load > self.inst.capacity + 1e-9:
                return False
        return len(seen) == self.inst.n_customers

    def build_mip(self, inst) -> "MIPModel":
        return MIPModel(inst, self)

    def to_assignment(self, sol) -> dict[str, float]:
        sol = _normalize_solution(sol)
        x = {name: 0.0 for name in MIPModel(self.inst, self).variables()}
        for route in sol:
            prev = 0
            for c in route:
                x[f"x_{prev}_{c}"] = 1.0
                prev = c
            x[f"x_{prev}_0"] = 1.0
        return x

    def from_assignment(self, x: dict[str, float]):
        succ = {}
        pred = {}
        for i in _nodes(self.inst):
            for j in _nodes(self.inst):
                if i == j:
                    continue
                if x.get(f"x_{i}_{j}", 0.0) > 0.5:
                    succ[i] = j
                    pred[j] = i

        routes = []
        starts = sorted(j for j in _customers(self.inst) if pred.get(j) == 0)
        used = set()
        for s in starts:
            if s in used:
                continue
            route = []
            cur = s
            while cur != 0 and cur not in used:
                route.append(cur)
                used.add(cur)
                cur = succ.get(cur, 0)
            if route:
                routes.append(tuple(route))
        routes.sort()
        return tuple(routes)

    def variable_groups(self, inst) -> dict[str, list[str]]:
        return {"arcs": MIPModel(inst, self).variables()}


class MIPModel:
    def __init__(self, inst, problem_model: ProblemModel | None = None):
        self.inst = inst
        self.problem_model = problem_model or ProblemModel(inst)
        self.last_objective: float | None = None

    def variables(self) -> list[str]:
        names = []
        for i in _nodes(self.inst):
            for j in _nodes(self.inst):
                if i != j:
                    names.append(f"x_{i}_{j}")
        return names

    def _build_pulp(self, fixed, integer, relaxed, near):
        inst = self.inst
        prob = pulp.LpProblem("CVRP", pulp.LpMinimize)

        x = {}
        for name in self.variables():
            if name in fixed:
                x[name] = pulp.LpVariable(name, lowBound=fixed[name], upBound=fixed[name], cat="Continuous")
            elif name in relaxed:
                x[name] = pulp.LpVariable(name, lowBound=0, upBound=1, cat="Continuous")
            else:
                x[name] = pulp.LpVariable(name, lowBound=0, upBound=1, cat="Binary" if name in integer or True else "Binary")

        # objective
        prob += pulp.lpSum(
            inst.dist(i, j) * x[f"x_{i}_{j}"]
            for i in _nodes(inst)
            for j in _nodes(inst)
            if i != j
        )

        # each customer exactly once in and out
        for c in _customers(inst):
            prob += pulp.lpSum(x[f"x_{i}_{c}"] for i in _nodes(inst) if i != c) == 1
            prob += pulp.lpSum(x[f"x_{c}_{j}"] for j in _nodes(inst) if j != c) == 1

        # depot balance (free number of vehicles)
        prob += pulp.lpSum(x[f"x_{0}_{j}"] for j in _customers(inst)) == pulp.lpSum(
            x[f"x_{i}_0"] for i in _customers(inst)
        )

        # flow variables for capacity and connectivity
        f = {}
        for i in _nodes(inst):
            for j in _nodes(inst):
                if i != j:
                    f[(i, j)] = pulp.LpVariable(f"f_{i}_{j}", lowBound=0, upBound=inst.capacity, cat="Continuous")

        total_demand = sum(inst.demand[c] for c in _customers(inst))

        # capacity linking
        for i in _nodes(inst):
            for j in _nodes(inst):
                if i != j:
                    prob += f[(i, j)] <= inst.capacity * x[f"x_{i}_{j}"]

        # flow conservation
        prob += (
            pulp.lpSum(f[(0, j)] for j in _customers(inst))
            - pulp.lpSum(f[(i, 0)] for i in _customers(inst))
            == total_demand
        )
        for c in _customers(inst):
            prob += (
                pulp.lpSum(f[(i, c)] for i in _nodes(inst) if i != c)
                - pulp.lpSum(f[(c, j)] for j in _nodes(inst) if j != c)
                == inst.demand[c]
            )

        if near is not None:
            xb, k = near
            prob += pulp.lpSum(
                (1 - x[v]) if xb.get(v, 0.0) > 0.5 else x[v] for v in self.variables()
            ) <= k

        return prob, x

    def solve(
        self,
        fixed: dict[str, float],
        integer: set[str],
        relaxed: set[str],
        time_limit: float,
        warm_start: dict[str, float] | None = None,
        near: tuple[dict[str, float], int] | None = None,
    ) -> dict[str, float] | None:
        prob, x = self._build_pulp(fixed, integer, relaxed, near)

        if warm_start is not None:
            for name, var in x.items():
                if name in warm_start:
                    var.setInitialValue(warm_start[name])

        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit)
        status = prob.solve(solver)
        if pulp.LpStatus[status] not in ("Optimal", "Feasible"):
            self.last_objective = None
            return None

        self.last_objective = float(pulp.value(prob.objective))
        return {name: float(pulp.value(var) or 0.0) for name, var in x.items()}


def build_problem_model(inst) -> ProblemModel:
    return ProblemModel(inst)


def trivial_solution(inst):
    return tuple((c,) for c in _customers(inst))
