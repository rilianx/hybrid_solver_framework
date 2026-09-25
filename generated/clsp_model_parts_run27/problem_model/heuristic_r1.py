from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import inf
from random import Random
from typing import Iterable

from examples.lotsizing.instance import CLSPInstance

COMPONENT = {
    "name": "clsp_heuristic_view",
    "slot": "solution_view",
    "compatible_skeletons": ["heuristic", "matheuristic"],
    "requires": [],
    "params": {
        "random_density": {"type": "float", "range": [0.0, 1.0]},
    },
}


def _as_bool_matrix(sol, n_items: int, n_periods: int) -> tuple[tuple[bool, ...], ...]:
    if sol is None:
        return tuple(tuple(False for _ in range(n_periods)) for _ in range(n_items))
    rows = []
    for i in range(n_items):
        row = sol[i]
        rows.append(tuple(bool(row[t]) for t in range(n_periods)))
    return tuple(rows)


def _setup_capacity(inst: CLSPInstance, sol: tuple[tuple[bool, ...], ...]) -> tuple[float, ...]:
    caps = []
    for t in range(inst.n_periods):
        used = 0.0
        for i in range(inst.n_items):
            if sol[i][t]:
                used += inst.setup_time[i]
        caps.append(inst.capacity[t] - used)
    return tuple(caps)


@dataclass
class _MCMFEdge:
    to: int
    rev: int
    cap: float
    cost: float


class _MinCostMaxFlow:
    def __init__(self, n: int):
        self.g: list[list[_MCMFEdge]] = [[] for _ in range(n)]

    def add_edge(self, u: int, v: int, cap: float, cost: float) -> None:
        fu = _MCMFEdge(v, len(self.g[v]), cap, cost)
        rv = _MCMFEdge(u, len(self.g[u]), 0.0, -cost)
        self.g[u].append(fu)
        self.g[v].append(rv)

    def min_cost_flow(self, s: int, t: int) -> tuple[float, float]:
        n = len(self.g)
        flow = 0.0
        cost = 0.0
        pot = [0.0] * n
        while True:
            dist = [inf] * n
            prev_v = [-1] * n
            prev_e = [-1] * n
            dist[s] = 0.0
            pq = [(0.0, s)]
            while pq:
                d, v = pq.pop(0) if False else __import__("heapq").heappop(pq)
                if d != dist[v]:
                    continue
                for ei, e in enumerate(self.g[v]):
                    if e.cap <= 1e-12:
                        continue
                    nd = d + e.cost + pot[v] - pot[e.to]
                    if nd + 1e-12 < dist[e.to]:
                        dist[e.to] = nd
                        prev_v[e.to] = v
                        prev_e[e.to] = ei
                        __import__("heapq").heappush(pq, (nd, e.to))
            if dist[t] == inf:
                break
            for v in range(n):
                if dist[v] < inf:
                    pot[v] += dist[v]
            add = inf
            v = t
            while v != s:
                u = prev_v[v]
                e = self.g[u][prev_e[v]]
                add = min(add, e.cap)
                v = u
            v = t
            while v != s:
                u = prev_v[v]
                e = self.g[u][prev_e[v]]
                e.cap -= add
                self.g[v][e.rev].cap += add
                cost += add * e.cost
                v = u
            flow += add
        return flow, cost


def _evaluate_plan(inst: CLSPInstance, sol: tuple[tuple[bool, ...], ...]) -> tuple[float, float, float]:
    n_items, n_periods = inst.n_items, inst.n_periods
    avail = _setup_capacity(inst, sol)
    if any(a < -1e-12 for a in avail):
        return 0.0, 0.0, sum(sum(row) for row in inst.demand)
    # Nodes:
    # source, period nodes, prod nodes (i,t), demand nodes (i,u), sink
    idx_source = 0
    idx_period = 1
    idx_prod = idx_period + n_periods
    idx_dem = idx_prod + n_items * n_periods
    idx_sink = idx_dem + n_items * n_periods
    mcmf = _MinCostMaxFlow(idx_sink + 1)

    def pnode(t: int) -> int:
        return idx_period + t

    def prod_node(i: int, t: int) -> int:
        return idx_prod + i * n_periods + t

    def dem_node(i: int, u: int) -> int:
        return idx_dem + i * n_periods + u

    BIG = 10**18
    for t in range(n_periods):
        if avail[t] > 1e-12:
            mcmf.add_edge(idx_source, pnode(t), avail[t], 0.0)
        for i in range(n_items):
            mcmf.add_edge(pnode(t), prod_node(i, t), BIG, 0.0)
    for i in range(n_items):
        for t in range(n_periods):
            for u in range(t, n_periods):
                mcmf.add_edge(prod_node(i, t), dem_node(i, u), BIG, inst.holding_cost[i] * (u - t))
        for u in range(n_periods):
            mcmf.add_edge(dem_node(i, u), idx_sink, inst.demand[i][u], 0.0)

    flow, inv_cost = mcmf.min_cost_flow(idx_source, idx_sink)
    total_demand = sum(sum(row) for row in inst.demand)
    unmet = max(0.0, total_demand - flow)
    setup_cost = sum(inst.setup_cost[i] for i in range(n_items) for t in range(n_periods) if sol[i][t])
    return unmet, setup_cost, inv_cost


class CLSPHeuristicView:
    def __init__(self, problem: CLSPInstance, random_density: float = 0.5):
        self.problem = problem
        self.random_density = random_density

    def canonical(self, sol):
        return canonical(sol)

    def trivial_solution(self, inst):
        return trivial_solution(inst)

    def random_solution(self, inst, rng):
        return random_solution(inst, rng, self.random_density)

    def from_answer(self, inst, answer):
        return from_answer(inst, answer)

    def violations(self, inst, sol) -> dict[str, float]:
        return violations(inst, sol)

    def cost_terms(self, inst, sol) -> dict[str, float]:
        return cost_terms(inst, sol)


def canonical(sol):
    if isinstance(sol, tuple) and all(isinstance(r, tuple) for r in sol):
        return tuple(tuple(bool(x) for x in row) for row in sol)
    raise TypeError("solution must be a tuple of tuples of bool")


def trivial_solution(inst):
    return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def random_solution(inst, rng: Random, random_density: float = 0.5):
    sol = tuple(
        tuple(rng.random() < random_density for _ in range(inst.n_periods))
        for _ in range(inst.n_items)
    )
    return canonical(sol)


def from_answer(inst, answer):
    return canonical(tuple(tuple(bool(v) for v in row) for row in answer))


def violations(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    unmet, _, _ = _evaluate_plan(inst, sol)
    return {"demanda": float(unmet)}


def cost_terms(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    unmet, setup_cost, inv_cost = _evaluate_plan(inst, sol)
    if unmet > 1e-9:
        return {"setup": float(setup_cost), "inventario": float(inv_cost)}
    return {"setup": float(setup_cost), "inventario": float(inv_cost)}


def build_component(problem, **params):
    random_density = params.get("random_density", 0.5)
    return CLSPHeuristicView(problem, random_density=random_density)
