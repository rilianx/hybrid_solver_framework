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
    return tuple(
        tuple(rng.random() < random_density for _ in range(n_periods))
        for _ in range(n_items)
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
    setup_term = 0.0

    for i in range(n_items):
        for t in range(n_periods):
            if sol[i][t]:
                setup_term += float(setup_cost[i])
                remaining_capacity[t] -= float(setup_time[i])

    total_demand = 0.0
    for i in range(n_items):
        for u in range(n_periods):
            total_demand += float(demand[i][u])

    if any(c < -1e-12 for c in remaining_capacity):
        return total_demand, setup_term, 0.0

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


def violations(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    unmet, _, _ = _evaluate_plan(inst, sol)
    if unmet > 1e-12:
        return {"demanda": float(unmet)}
    return {}


def cost_terms(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    unmet, setup_term, inv_cost = _evaluate_plan(inst, sol)
    terms = {
        "setup": float(setup_term),
        "inventario": float(inv_cost),
    }
    if unmet > 1e-12:
        terms["penalizacion_demanda"] = float(unmet)
    return terms


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


def build_component(problem, **params):
    random_density = params.get("random_density", 0.5)
    return CLSPHeuristicView(problem, random_density=random_density)


# ---- vista MIP ----
from typing import Dict, List, Tuple

from examples.lotsizing.instance import CLSPInstance


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


def _canonical(sol):
    if sol is None:
        return None
    return tuple(tuple(bool(v) for v in row) for row in sol)


def _big_m(inst) -> float:
    demand = _demand(inst)
    capacity = _capacity(inst)
    m = 1.0
    for i in range(_n_items(inst)):
        m = max(m, sum(float(d) for d in demand[i]))
    for t in range(_n_periods(inst)):
        m = max(m, float(capacity[t]))
    return m


def variables(inst) -> dict[str, tuple[float, float, str]]:
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    vars_: dict[str, tuple[float, float, str]] = {}

    for i in range(n_items):
        for t in range(n_periods):
            vars_[f"y_{i}_{t}"] = (0.0, 1.0, "binary")

    big = _big_m(inst)
    for i in range(n_items):
        for t in range(n_periods):
            vars_[f"q_{i}_{t}"] = (0.0, big, "continuous")
            vars_[f"inv_{i}_{t}"] = (0.0, big, "continuous")
    return vars_


def structural_variables(inst) -> list[str]:
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    return [f"y_{i}_{t}" for i in range(n_items) for t in range(n_periods)]


def _evaluate_plan(inst: CLSPInstance, sol) -> dict[str, object] | None:
    sol = _canonical(sol)
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    demand = _demand(inst)
    setup_cost = _setup_cost(inst)
    holding_cost = _holding_cost(inst)
    setup_time = _setup_time(inst)
    capacity = _capacity(inst)

    remaining_capacity = [float(capacity[t]) for t in range(n_periods)]
    setup_term = 0.0
    for i in range(n_items):
        for t in range(n_periods):
            if sol[i][t]:
                setup_term += float(setup_cost[i])
                remaining_capacity[t] -= float(setup_time[i])

    if any(c < -1e-12 for c in remaining_capacity):
        return None

    src = 0
    period0 = 1
    prod0 = period0 + n_periods
    dem0 = prod0 + n_items * n_periods
    sink = dem0 + n_items * n_periods

    class _Edge:
        __slots__ = ("to", "rev", "cap", "cost")

        def __init__(self, to: int, rev: int, cap: float, cost: float):
            self.to = to
            self.rev = rev
            self.cap = cap
            self.cost = cost

    class _MCF:
        def __init__(self, n: int):
            self.g = [[] for _ in range(n)]

        def add_edge(self, u: int, v: int, cap: float, cost: float) -> None:
            self.g[u].append(_Edge(v, len(self.g[v]), cap, cost))
            self.g[v].append(_Edge(u, len(self.g[u]) - 1, 0.0, -cost))

        def min_cost_flow(self, s: int, t: int) -> tuple[float, float]:
            import heapq
            from math import inf

            n = len(self.g)
            pot = [0.0] * n
            flow = 0.0
            cost = 0.0
            while True:
                dist = [inf] * n
                pv = [-1] * n
                pe = [-1] * n
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
                            pv[e.to] = v
                            pe[e.to] = ei
                            heapq.heappush(pq, (nd, e.to))
                if dist[t] == float("inf"):
                    break
                for v in range(n):
                    if dist[v] < float("inf"):
                        pot[v] += dist[v]
                add = float("inf")
                v = t
                while v != s:
                    u = pv[v]
                    e = self.g[u][pe[v]]
                    add = min(add, e.cap)
                    v = u
                v = t
                while v != s:
                    u = pv[v]
                    e = self.g[u][pe[v]]
                    e.cap -= add
                    self.g[v][e.rev].cap += add
                    cost += add * e.cost
                    v = u
                flow += add
            return flow, cost

    def pnode(t: int) -> int:
        return period0 + t

    def prnode(i: int, t: int) -> int:
        return prod0 + i * n_periods + t

    def dnode(i: int, u: int) -> int:
        return dem0 + i * n_periods + u

    mcf = _MCF(sink + 1)
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
    total_demand = sum(float(demand[i][u]) for i in range(n_items) for u in range(n_periods))
    unmet = max(0.0, total_demand - flow)

    q = [[0.0 for _ in range(n_periods)] for _ in range(n_items)]
    inv = [[0.0 for _ in range(n_periods)] for _ in range(n_items)]
    for t in range(n_periods):
        for i in range(n_items):
            if not sol[i][t]:
                continue
            node = prnode(i, t)
            shipped = 0.0
            for e in mcf.g[node]:
                if dem0 <= e.to < sink:
                    rev = mcf.g[e.to][e.rev]
                    shipped += float(rev.cap)
            q[i][t] = shipped

    for i in range(n_items):
        prev = 0.0
        for t in range(n_periods):
            prev = prev + q[i][t] - float(demand[i][t])
            inv[i][t] = max(0.0, prev)

    return {
        "unmet": unmet,
        "setup": setup_term,
        "inventario": inv_cost,
        "q": q,
        "inv": inv,
    }


def to_assignment(inst, sol) -> dict[str, float]:
    sol = _canonical(sol)
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    assign: dict[str, float] = {}
    for i in range(n_items):
        for t in range(n_periods):
            assign[f"y_{i}_{t}"] = 1.0 if sol[i][t] else 0.0
    return assign


def aux_values(inst, sol) -> dict[str, float]:
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    evaluated = _evaluate_plan(inst, sol)
    aux: dict[str, float] = {}
    if evaluated is None:
        for i in range(n_items):
            for t in range(n_periods):
                aux[f"q_{i}_{t}"] = 0.0
                aux[f"inv_{i}_{t}"] = 0.0
        return aux
    q = evaluated["q"]
    inv = evaluated["inv"]
    for i in range(n_items):
        for t in range(n_periods):
            aux[f"q_{i}_{t}"] = float(q[i][t])
            aux[f"inv_{i}_{t}"] = float(inv[i][t])
    return aux


def from_assignment(inst, x) -> "sol":
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    return tuple(
        tuple(bool(round(float(x.get(f"y_{i}_{t}", 0.0)))) for t in range(n_periods))
        for i in range(n_items)
    )


def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    demand = _demand(inst)
    setup_time = _setup_time(inst)
    capacity = _capacity(inst)
    big = _big_m(inst)

    fams: dict[str, list[tuple[dict[str, float], str, float]]] = {
        "demanda": [],
        "capacidad": [],
        "vinculo": [],
    }

    for i in range(n_items):
        coeff: dict[str, float] = {}
        rhs = 0.0
        for u in range(n_periods):
            coeff[f"q_{i}_{u}"] = 1.0
            rhs += float(demand[i][u])
        fams["demanda"].append((coeff, ">=", rhs))

    for t in range(n_periods):
        coeff = {f"q_{i}_{t}": 1.0 for i in range(n_items)}
        for i in range(n_items):
            coeff[f"y_{i}_{t}"] = coeff.get(f"y_{i}_{t}", 0.0) + float(setup_time[i])
        fams["capacidad"].append((coeff, "<=", float(capacity[t])))

    for i in range(n_items):
        for t in range(n_periods):
            fams["vinculo"].append(({f"q_{i}_{t}": 1.0, f"y_{i}_{t}": -big}, "<=", 0.0))

    return fams


def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]:
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    setup_cost = _setup_cost(inst)
    holding_cost = _holding_cost(inst)

    coeff_setup: dict[str, float] = {}
    coeff_inv: dict[str, float] = {}
    for i in range(n_items):
        for t in range(n_periods):
            coeff_setup[f"y_{i}_{t}"] = float(setup_cost[i])
            coeff_inv[f"inv_{i}_{t}"] = float(holding_cost[i])

    return {
        "setup": (coeff_setup, 0.0),
        "inventario": (coeff_inv, 0.0),
    }


def variable_groups(inst) -> dict[str, list[str]]:
    n_items = _n_items(inst)
    n_periods = _n_periods(inst)
    groups = {"g0": [], "g1": [], "g2": [], "g3": []}
    for i in range(n_items):
        for t in range(n_periods):
            groups[f"g{(i % 2) * 2 + (t % 2)}"].append(f"y_{i}_{t}")
    return groups


class CLSPMIPView:
    def __init__(self, problem):
        self.problem = problem

    def variables(self, inst):
        return variables(inst)

    def structural_variables(self, inst):
        return structural_variables(inst)

    def to_assignment(self, inst, sol):
        return to_assignment(inst, sol)

    def aux_values(self, inst, sol):
        return aux_values(inst, sol)

    def from_assignment(self, inst, x):
        return from_assignment(inst, x)

    def constraint_families(self, inst):
        return constraint_families(inst)

    def objective_terms(self, inst):
        return objective_terms(inst)

    def variable_groups(self, inst):
        return variable_groups(inst)
