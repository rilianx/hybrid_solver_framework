"""`ProblemModel` del segundo problema: ruteo de vehículos con capacidad (CVRP), flota libre.

Está para probar que los contratos del framework no están sobreajustados al CLSP. Las
diferencias que importan:

- La vista estructural es una lista de rutas, no una matriz binaria.
- `delta` es barato: mover un cliente cambia tres o cuatro distancias. En el CLSP cada
  evaluación era un LP de ~15 ms.
- La factibilidad es local (la carga de cada ruta), y con flota libre siempre existe
  una solución factible: una ruta por cliente.

Vista estructural (`Solution`): tupla de rutas; cada ruta, una tupla de clientes
`1..n` (el depósito es 0 y no aparece). Forma canónica, que exige el puente con el MIP
(`from_assignment(to_assignment(sol)) == sol`): sin rutas vacías y ordenadas por su
primer cliente. `canonical(routes)` la produce desde cualquier lista de rutas.

Objetivo: distancia total (euclidiana). Una solución infactible no se rechaza, se
penaliza (exceso de carga, clientes que faltan o se repiten), así que el objetivo
siempre es finito.

Vista de asignación: arcos binarios `x_i_j` (i ≠ j, 0 = depósito). El MIP es la
formulación de dos índices con cargas MTZ.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from random import Random

import pulp

Route = tuple[int, ...]
Solution = tuple[Route, ...]


def canonical(routes) -> Solution:
    """Forma canónica: sin rutas vacías, ordenadas por su primer cliente."""
    return tuple(sorted((tuple(r) for r in routes if r), key=lambda r: r[0]))


def var_name(i: int, j: int) -> str:
    return f"x_{i}_{j}"


@dataclass(frozen=True)
class CVRPInstance:
    coords: tuple[tuple[float, float], ...]  # coords[0] = depósito
    demand: tuple[float, ...]  # demand[0] = 0
    capacity: float

    @property
    def n_customers(self) -> int:
        return len(self.coords) - 1

    @property
    def customers(self) -> range:
        return range(1, len(self.coords))

    def dist(self, i: int, j: int) -> float:
        (xi, yi), (xj, yj) = self.coords[i], self.coords[j]
        return math.hypot(xi - xj, yi - yj)

    @staticmethod
    def random(n_customers: int, rng: Random, route_size: float = 5.0, clustered: bool = False) -> "CVRPInstance":
        """Clientes en [0, 100]², depósito en el centro, demandas 1–10. La capacidad se fija
        para que una ruta atienda en promedio `route_size` clientes. `clustered=True` agrupa
        a los clientes en 3–5 centros (como las instancias C de Solomon / X de Uchoa)."""
        coords = [(50.0, 50.0)]
        if clustered:
            centers = [(rng.uniform(10, 90), rng.uniform(10, 90)) for _ in range(rng.randint(3, 5))]
            for _ in range(n_customers):
                cx, cy = rng.choice(centers)
                coords.append((min(100.0, max(0.0, rng.gauss(cx, 8))), min(100.0, max(0.0, rng.gauss(cy, 8)))))
        else:
            coords += [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n_customers)]
        coords = [(round(x, 1), round(y, 1)) for x, y in coords]
        demand = [0.0] + [float(rng.randint(1, 10)) for _ in range(n_customers)]
        capacity = float(max(max(demand), round(route_size * sum(demand) / n_customers)))
        return CVRPInstance(tuple(coords), tuple(demand), capacity)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(f"{self.n_customers} {self.capacity}\n")
            for (x, y), d in zip(self.coords, self.demand):
                f.write(f"{x} {y} {d}\n")

    @staticmethod
    def load(path: str) -> "CVRPInstance":
        with open(path) as f:
            n, cap = f.readline().split()
            rows = [tuple(map(float, line.split())) for line in f if line.strip()]
        assert len(rows) == int(n) + 1
        return CVRPInstance(tuple((x, y) for x, y, _ in rows), tuple(d for _, _, d in rows), float(cap))


def route_length(inst: CVRPInstance, route: Route) -> float:
    if not route:
        return 0.0
    total, prev = 0.0, 0
    for c in route:
        total += inst.dist(prev, c)
        prev = c
    return total + inst.dist(prev, 0)


def route_load(inst: CVRPInstance, route: Route) -> float:
    return sum(inst.demand[c] for c in route)


def penalty_weight(inst: CVRPInstance) -> float:
    """Penalización por unidad de exceso de carga o por cliente faltante/repetido: mayor que
    cualquier ahorro de distancia posible (el doble del diámetro por cliente)."""
    diam = max(inst.dist(i, j) for i in range(len(inst.coords)) for j in range(len(inst.coords)))
    return 2.0 * diam * max(1, inst.n_customers)


class CVRPModel:
    """Implementa `core.contracts.ProblemModel` para una instancia fija (`self.inst`)."""

    # Sugerencias propias del CVRP para los mensajes del validador (`core.validation.quality.hint`).
    validation_hints = {
        "novelty": ("P.ej. intercambiar dos clientes de rutas distintas, mover un tramo de varios clientes seguidos a otra "
                    "ruta, invertir un tramo dentro de una ruta, o cruzar las colas de dos rutas (2-opt*)."),
        "distinct": ("En el CVRP: si trabaja dentro de una ruta o entre rutas, si mueve un cliente o un tramo, si usa la "
                     "cercanía geométrica o la holgura de carga."),
        "constructor_probe": ("Revisa que cada ruta respete la capacidad y que todos los clientes queden atendidos exactamente "
                              "una vez; con flota libre siempre se puede abrir otra ruta."),
        "constructor_quality": "Evita rutas con un solo cliente cuando cabe en una ruta cercana.",
    }

    def __init__(self, inst: CVRPInstance):
        self.inst = inst
        self._penalty = penalty_weight(inst)

    def load(self, path: str) -> CVRPInstance:
        return CVRPInstance.load(path)

    def violations(self, sol: Solution) -> tuple[float, int]:
        """(exceso de carga total, clientes faltantes + repetidos)."""
        inst = self.inst
        excess = sum(max(0.0, route_load(inst, r) - inst.capacity) for r in sol)
        seen: dict[int, int] = {}
        for r in sol:
            for c in r:
                seen[c] = seen.get(c, 0) + 1
        bad = sum(1 for c in inst.customers if seen.get(c, 0) != 1) + sum(1 for c in seen if c not in inst.customers)
        return excess, bad

    def distance(self, sol: Solution) -> float:
        return sum(route_length(self.inst, r) for r in sol)

    def objective(self, sol: Solution) -> float:
        excess, bad = self.violations(sol)
        return self.distance(sol) + self._penalty * (excess + bad)

    def is_feasible(self, sol: Solution) -> bool:
        excess, bad = self.violations(sol)
        return excess <= 1e-9 and bad == 0

    def explain_infeasibility(self, sol: Solution) -> str:
        inst = self.inst
        parts = [f"ruta {k} carga {route_load(inst, r):g} > capacidad {inst.capacity:g}"
                 for k, r in enumerate(sol) if route_load(inst, r) > inst.capacity + 1e-9]
        seen: dict[int, int] = {}
        for r in sol:
            for c in r:
                seen[c] = seen.get(c, 0) + 1
        missing = [c for c in inst.customers if c not in seen]
        repeated = [c for c, k in seen.items() if k > 1]
        if missing:
            parts.append(f"clientes sin visitar: {missing[:8]}")
        if repeated:
            parts.append(f"clientes repetidos: {repeated[:8]}")
        return "; ".join(parts) or "factible"

    # --- puente hacia lo matemático ---
    def build_mip(self, inst: CVRPInstance) -> "CVRPMip":
        return CVRPMip(inst)

    def to_assignment(self, sol: Solution) -> dict[str, float]:
        x = {v: 0.0 for v in all_arcs(self.inst)}
        for r in sol:
            nodes = (0, *r, 0)
            for a, b in zip(nodes, nodes[1:]):
                x[var_name(a, b)] = 1.0
        return x

    def from_assignment(self, x: dict[str, float]) -> Solution:
        succ: dict[int, list[int]] = {}
        for name, v in x.items():
            if v is not None and round(v) >= 1:
                _, a, b = name.split("_")
                succ.setdefault(int(a), []).append(int(b))
        routes = []
        for first in sorted(succ.get(0, [])):
            route, cur, guard = [], first, 0
            while cur != 0 and guard <= self.inst.n_customers:
                route.append(cur)
                nxt = succ.get(cur, [0])
                cur = nxt[0]
                guard += 1
            routes.append(tuple(route))
        return canonical(routes)

    def variable_groups(self, inst: CVRPInstance) -> dict[str, list[str]]:
        """Arcos agrupados por sector angular del cliente de salida (los que salen del depósito,
        con el sector del cliente de llegada): 4 clientes por sector, en orden de ángulo."""
        order = sorted(inst.customers, key=lambda c: math.atan2(inst.coords[c][1] - inst.coords[0][1],
                                                                  inst.coords[c][0] - inst.coords[0][0]))
        sector = {c: k // 4 for k, c in enumerate(order)}
        groups: dict[str, list[str]] = {f"s{k}": [] for k in range(max(sector.values()) + 1)}  # en orden angular
        for name in all_arcs(inst):
            _, a, b = name.split("_")
            owner = int(a) if int(a) != 0 else int(b)
            groups[f"s{sector[owner]}"].append(name)
        return groups

    def construction_view(self, inst: CVRPInstance):
        from .construction import CVRPConstructionView

        return CVRPConstructionView(self, inst)


def all_arcs(inst: CVRPInstance) -> list[str]:
    nodes = range(len(inst.coords))
    return [var_name(i, j) for i in nodes for j in nodes if i != j]


class CVRPMip:
    """`core.mip.MIPModel`: formulación de dos índices con cargas MTZ (PuLP/CBC).

    Flota libre: tantos arcos saliendo del depósito como entrando. Carga u_i ∈ [d_i, Q] y
    u_j ≥ u_i + d_j − Q(1 − x_ij) entre clientes (elimina subtours y limita la carga).
    """

    def __init__(self, inst: CVRPInstance):
        self.inst = inst
        self.last_objective: float | None = None

    def variables(self) -> list[str]:
        return all_arcs(self.inst)

    def solve(self, fixed, integer, relaxed, time_limit, warm_start=None, near=None):
        inst = self.inst
        V = range(len(inst.coords))
        C = list(inst.customers)
        prob = pulp.LpProblem("cvrp", pulp.LpMinimize)
        x = {}
        for i in V:
            for j in V:
                if i == j:
                    continue
                name = var_name(i, j)
                if name in fixed:
                    v = int(round(fixed[name]))
                    x[i, j] = pulp.LpVariable(name, lowBound=v, upBound=v, cat="Continuous")
                elif name in relaxed:
                    x[i, j] = pulp.LpVariable(name, lowBound=0, upBound=1, cat="Continuous")
                else:
                    x[i, j] = pulp.LpVariable(name, cat="Binary")
                    if warm_start and name in warm_start:
                        x[i, j].setInitialValue(int(round(warm_start[name])))
        u = {i: pulp.LpVariable(f"u_{i}", lowBound=inst.demand[i], upBound=inst.capacity) for i in C}
        prob += pulp.lpSum(inst.dist(i, j) * x[i, j] for (i, j) in x)
        for i in C:
            prob += pulp.lpSum(x[i, j] for j in V if j != i) == 1
            prob += pulp.lpSum(x[j, i] for j in V if j != i) == 1
        prob += pulp.lpSum(x[0, j] for j in C) == pulp.lpSum(x[j, 0] for j in C)
        Q = inst.capacity
        for i in C:
            for j in C:
                if i != j:
                    prob += u[j] >= u[i] + inst.demand[j] - Q * (1 - x[i, j])
        if near is not None:
            x_bar, k = near
            prob += pulp.lpSum((1 - x[i, j]) if round(x_bar.get(var_name(i, j), 0.0)) >= 1 else x[i, j]
                               for (i, j) in x if var_name(i, j) not in fixed) <= k
        prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=max(0.1, float(time_limit)), warmStart=bool(warm_start)))
        self.last_objective = None
        if pulp.LpStatus[prob.status] not in ("Optimal", "Not Solved"):
            return None
        vals = {var_name(i, j): v.value() for (i, j), v in x.items()}
        if any(val is None for val in vals.values()):
            return None
        self.last_objective = float(pulp.value(prob.objective))
        return {k: (float(v) if k in relaxed else float(round(v))) for k, v in vals.items()}


# Re-export: los puntajes (`greedy_score`) importan los tipos de la vista constructiva desde
# el módulo del problema, como en el CLSP.
from .construction import CVRPPartial, InsertAction  # noqa: E402,F401
