from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from math import inf
from typing import Any, Iterable

COMPONENT = {
    "name": "cvrp_structural_mip_view",
    "slot": "problem_model",
    "compatible_skeletons": ["generic_hybrid", "matheuristic_hybrid"],
    "requires": [],
    "params": {},
}


def _all_nodes(inst) -> range:
    return range(0, inst.n_customers + 1)


def _route_distance(inst, route: tuple[int, ...]) -> float:
    if not route:
        return 0.0
    d = inst.dist(0, route[0]) + inst.dist(route[-1], 0)
    for i in range(len(route) - 1):
        d += inst.dist(route[i], route[i + 1])
    return d


def _solution_distance(inst, sol: tuple[tuple[int, ...], ...]) -> float:
    return sum(_route_distance(inst, r) for r in sol)


def _solution_load(inst, route: tuple[int, ...]) -> float:
    return sum(inst.demand[c] for c in route)


def _is_solution_canonical(sol: tuple[tuple[int, ...], ...]) -> bool:
    if not isinstance(sol, tuple):
        return False
    prev = None
    seen = set()
    for r in sol:
        if not isinstance(r, tuple):
            return False
        if len(r) == 0:
            return False
        if prev is not None and r < prev:
            return False
        prev = r
        for c in r:
            if c in seen:
                return False
            seen.add(c)
    return True


class ProblemModel:
    def __init__(self, inst):
        self.inst = inst

    def objective(self, sol) -> float:
        if not isinstance(sol, tuple):
            sol = tuple(sol)
        dist = 0.0
        seen = set()
        cap_violation = 0.0
        miss = 0
        bad = 0
        for route in sol:
            if not isinstance(route, tuple) or len(route) == 0:
                bad += 1
                continue
            load = 0.0
            prev = 0
            for c in route:
                if c == 0 or c > self.inst.n_customers or c in seen:
                    bad += 1
                seen.add(c)
                load += self.inst.demand[c]
                dist += self.inst.dist(prev, c)
                prev = c
            dist += self.inst.dist(prev, 0)
            if load > self.inst.capacity:
                cap_violation += load - self.inst.capacity
        for c in self.inst.customers:
            if c not in seen:
                miss += 1
        penalty = 1_000_000.0 * (bad + miss) + 10_000.0 * cap_violation
        return dist + penalty

    def is_feasible(self, sol) -> bool:
        if not isinstance(sol, tuple):
            return False
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
        return MIPModel(inst)

    def to_assignment(self, sol) -> dict[str, float]:
        if not isinstance(sol, tuple):
            sol = tuple(sol)
        x: dict[str, float] = {}
        nodes = list(_all_nodes(self.inst))
        for i in nodes:
            for j in nodes:
                if i == j:
                    continue
                x[f"x_{i}_{j}"] = 0.0

        for route in sol:
            prev = 0
            for c in route:
                x[f"x_{prev}_{c}"] = 1.0
                prev = c
            x[f"x_{prev}_0"] = 1.0
        return x

    def from_assignment(self, x: dict[str, float]):
        n = self.inst.n_customers
        succ = {}
        pred = {}
        for i in range(n + 1):
            for j in range(n + 1):
                if i == j:
                    continue
                if x.get(f"x_{i}_{j}", 0.0) > 0.5:
                    succ[i] = j
                    pred[j] = i

        routes = []
        starts = [j for j in range(1, n + 1) if pred.get(j, None) == 0]
        starts.sort()
        used = set()
        for s in starts:
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
        vars_ = self.build_mip(inst).variables()
        return {"arcs": vars_}


class MIPModel:
    def __init__(self, inst):
        self.inst = inst
        self.last_objective: float | None = None

    def variables(self) -> list[str]:
        names = []
        n = self.inst.n_customers
        for i in range(n + 1):
            for j in range(n + 1):
                if i != j:
                    names.append(f"x_{i}_{j}")
        return names

    def _assignment_ok(self, x: dict[str, float], fixed: dict[str, float]) -> bool:
        for k, v in fixed.items():
            if abs(x.get(k, 0.0) - v) > 1e-9:
                return False
        n = self.inst.n_customers
        outdeg = {i: 0 for i in range(n + 1)}
        indeg = {i: 0 for i in range(n + 1)}
        for i in range(n + 1):
            for j in range(n + 1):
                if i == j:
                    continue
                if x.get(f"x_{i}_{j}", 0.0) > 0.5:
                    outdeg[i] += 1
                    indeg[j] += 1
        for c in range(1, n + 1):
            if indeg[c] != 1 or outdeg[c] != 1:
                return False
        if outdeg[0] != indeg[0]:
            return False
        return True

    def _near_ok(self, x: dict[str, float], near):
        if near is None:
            return True
        xb, k = near
        dist = 0
        for var in self.variables():
            if (xb.get(var, 0.0) > 0.5) != (x.get(var, 0.0) > 0.5):
                dist += 1
                if dist > k:
                    return False
        return True

    def solve(
        self,
        fixed: dict[str, float],
        integer: set[str],
        relaxed: set[str],
        time_limit: float,
        warm_start: dict[str, float] | None = None,
        near: tuple[dict[str, float], int] | None = None,
    ) -> dict[str, float] | None:
        vars_ = self.variables()
        n = self.inst.n_customers
        best_x = None
        best_obj = inf

        customers = tuple(range(1, n + 1))
        for perm in permutations(customers):
            for mask in range(1 << (n - 1)) if n > 1 else [0]:
                sol = []
                cur = [perm[0]]
                load = self.inst.demand[perm[0]]
                ok = True
                for idx in range(1, n):
                    c = perm[idx]
                    if load + self.inst.demand[c] > self.inst.capacity + 1e-9:
                        ok = False
                        break
                    cur.append(c)
                    load += self.inst.demand[c]
                    if idx < n and ((mask >> (idx - 1)) & 1):
                        sol.append(tuple(cur))
                        cur = []
                        if idx < n:
                            pass
                if not ok:
                    continue
                if cur:
                    sol.append(tuple(cur))
                sol = tuple(sol)
                if not self.is_feasible(sol):
                    continue
                x = self.inst_model.to_assignment(sol) if hasattr(self, "inst_model") else self._to_assignment(sol)
                if not self._assignment_ok(x, fixed):
                    continue
                if not self._near_ok(x, near):
                    continue
                obj = self.inst_model.objective(sol) if hasattr(self, "inst_model") else self._objective(sol)
                if obj < best_obj:
                    best_obj = obj
                    best_x = x
        self.last_objective = best_obj if best_x is not None else None
        if best_x is None:
            return None
        return {v: float(best_x.get(v, 0.0)) for v in vars_}

    def _objective(self, sol):
        dist = 0.0
        for route in sol:
            prev = 0
            for c in route:
                dist += self.inst.dist(prev, c)
                prev = c
            dist += self.inst.dist(prev, 0)
        return dist

    def _to_assignment(self, sol):
        x = {v: 0.0 for v in self.variables()}
        for route in sol:
            prev = 0
            for c in route:
                x[f"x_{prev}_{c}"] = 1.0
                prev = c
            x[f"x_{prev}_0"] = 1.0
        return x

    def is_feasible(self, sol) -> bool:
        return ProblemModel(self.inst).is_feasible(sol)


def build_problem_model(inst) -> ProblemModel:
    model = ProblemModel(inst)
    return model


def trivial_solution(inst):
    return tuple((c,) for c in inst.customers)
