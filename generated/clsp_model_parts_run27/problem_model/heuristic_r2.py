from __future__ import annotations

from dataclasses import dataclass
from math import inf
from random import Random
import heapq

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


def _get_attr(inst, *names):
    for name in names:
        if hasattr(inst, name):
            return getattr(inst, name)
    raise AttributeError(f"instance missing any of attributes {names}")


def _n_items(inst) -> int:
    return int(_get_attr(inst, "n_items"))


def _n_periods(inst) -> int:
    return int(_get_attr(inst, "n_periods"))


def _demand(inst):
    return _get_attr(inst, "demand")


def _setup_cost(inst):
    return _get_attr(inst, "setup_cost", "s")


def _holding_cost(inst):
    return _get_attr(inst, "holding_cost", "h")


def _setup_time(inst):
    return _get_attr(inst, "setup_time", "st")


def _capacity(inst):
    return _get_attr(inst, "capacity", "cap")


def canonical(sol):
    if sol is None:
        return None
    return tuple(tuple(bool(v) for v in row) for row in sol)


def trivial_solution(inst):
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    return tuple(tuple(True for _ in range(n_periods)) for _ in range(n_items))


def random_solution(inst, rng: Random, random_density: float = 0.5):
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    return canonical(
        tuple(
            tuple(rng.random() < random_density for _ in range(n_periods))
            for _ in range(n_items)
        )
    )


def from_answer(inst, answer):
    return canonical(answer)


@dataclass
class _Edge:
    to: int
    rev: int
    cap: float
    cost: float


class _MinCostFlow:
    def __init__(self, n: int):
        self.g = [[] for _ in range(n)]

    def add_edge(self, u: int, v: int, cap: float, cost: float) -> None:
        self.g[u].append(_Edge(v, len(self.g[v]), cap, cost))
        self.g[v].append(_Edge(u, len(self.g[u]) - 1, 0.0, -cost))

    def min_cost_flow(self, s: int, t: int) -> tuple[float, float]:
        n = len(self.g)
        pot = [0.0] * n
        flow = 0.0
        cost = 0.0
        while True:
            dist = [inf] * n
            prev_v = [-1] * n
            prev_e = [-1] * n
            dist[s] = 0.0
            pq = [(0.0, s)]
            while pq:
                d, v = heapq.heappop(pq)
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
                        heapq.heappush(pq, (nd, e.to))
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
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    demand = _demand(inst)
    setup_cost = _setup_cost(inst)
    holding_cost = _holding_cost(inst)
    setup_time = _setup_time(inst)
    capacity = _capacity(inst)

    remaining_capacity = [float(capacity[t]) for t in range(n_periods)]
    for t in range(n_periods):
        used = 0.0
        for i in range(n_items):
            if sol[i][t]:
                used += float(setup_time[i])
        remaining_capacity[t] -= used

    setup_term = 0.0
    for i in range(n_items):
        for t in range(n_periods):
            if sol[i][t]:
                setup_term += float(setup_cost[i])

    if any(c < -1e-12 for c in remaining_capacity):
        total_demand = sum(sum(row) for row in demand)
        return total_demand, setup_term, 0.0

    # Min-cost flow:
    # source -> period nodes -> production nodes (i,t) only if setup exists -> demand nodes (i,u) -> sink
    src = 0
    period0 = 1
    prod0 = period0 + n_periods
    dem0 = prod0 + n_items * n_periods
    sink = dem0 + n_items * n_periods
    mcf = _MinCostFlow(sink + 1)

    def pnode(t: int) -> int:
        return period0 + t

    def prnode(i: int, t: int) -> int:
        return prod0 + i * n_periods + t

    def dnode(i: int, u: int) -> int:
        return dem0 + i * n_periods + u

    total_demand = 0.0
    for i in range(n_items):
        for u in range(n_periods):
            total_demand += float(demand[i][u])

    for t in range(n_periods):
        if remaining_capacity[t] > 1e-12:
            mcf.add_edge(src, pnode(t), remaining_capacity[t], 0.0)

    BIG = 10**18
    for t in range(n_periods):
        for i in range(n_items):
            if sol[i][t]:
                mcf.add_edge(pnode(t), prnode(i, t), BIG, 0.0)

    for i in range(n_items):
        for t in range(n_periods):
            for u in range(t, n_periods):
                mcf.add_edge(prnode(i, t), dnode(i, u), BIG, float(holding_cost[i]) * (u - t))
        for u in range(n_periods):
            qty = float(demand[i][u])
            if qty > 0:
                mcf.add_edge(dnode(i, u), sink, qty, 0.0)

    flow, inv_cost = mcf.min_cost_flow(src, sink)
    unmet = max(0.0, total_demand - flow)
    return unmet, setup_term, inv_cost


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
        sol = canonical(sol)
        unmet, _, _ = _evaluate_plan(inst, sol)
        return {"demanda": float(unmet)} if unmet > 1e-12 else {}

    def cost_terms(self, inst, sol) -> dict[str, float]:
        sol = canonical(sol)
        unmet, setup_term, inv_cost = _evaluate_plan(inst, sol)
        total = float(setup_term + inv_cost)
        if unmet > 1e-12:
            return {"setup": float(setup_term), "inventario": float(inv_cost), "penalizacion_demanda": float(unmet)}
        return {"setup": float(setup_term), "inventario": float(inv_cost), "total": total}


def build_component(problem, **params):
    random_density = params.get("random_density", 0.5)
    return CLSPHeuristicView(problem, random_density=random_density)
