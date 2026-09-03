"""`ProblemModel` del piloto con estructura temporal: lot sizing capacitado
multi-ítem (CLSP, un nivel, sin backlog), el problema sugerido en §9.2.

Vista estructural: la **matriz de setups** `y[i][t] ∈ {0,1}` (tupla de
tuplas). Dadas las decisiones de setup, cantidades e inventarios se
obtienen con un LP; por eso `objective(sol)` resuelve ese LP (con
cache). Se agrega una variable de faltante `u[i][t]` con penalidad alta
para que la evaluación sea siempre finita: un plan de setups que no
alcanza a cubrir la demanda no se rechaza, se penaliza de forma
graduada, lo que da gradiente a las heurísticas.

Vista de asignación: `{"y_i_t": 0/1}`. `variable_groups` agrupa por
período — la estructura que Relax-and-Fix (ventanas) y Fix-and-Optimize
(bloques) explotan, y que knapsack no tenía.

`CLSPMip` implementa `core.mip.MIPModel`: un único punto de contacto
con PuLP/CBC para todas las matheurísticas.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

import pulp

Solution = tuple[tuple[bool, ...], ...]  # y[i][t]

SHORTAGE_PENALTY = 1000.0  # valor de referencia; ver `shortage_penalty(inst)`


def shortage_penalty(inst: "CLSPInstance") -> float:
    """Penalización por unidad de faltante, relativa a la instancia.

    Debe ser tal que **ninguna** reducción de costo legítima (ahorrarse un
    setup, vaciar inventario) compense dejar demanda sin cubrir; si no, la
    búsqueda descubre que "un poco de faltante" es rentable y devuelve planes
    infactibles con mejor objetivo penalizado (ocurrió con LNS-MIP en
    instancias Trigeiro, donde un setup ≈ 1000 = la penalización fija).
    Regla: 20 × (setup más caro + inventario de una unidad durante todo el
    horizonte), con piso 1000, por unidad.
    """
    worst_setup = max(inst.setup_cost) if inst.setup_cost else 0.0
    worst_hold = (max(inst.holding_cost) if inst.holding_cost else 0.0) * inst.n_periods
    return max(1000.0, 20.0 * (worst_setup + worst_hold))


@dataclass(frozen=True)
class CLSPInstance:
    demand: tuple[tuple[float, ...], ...]  # d[i][t]
    setup_cost: tuple[float, ...]  # s[i]
    holding_cost: tuple[float, ...]  # h[i]
    setup_time: tuple[float, ...]  # st[i]
    capacity: tuple[float, ...]  # cap[t]

    @property
    def n_items(self) -> int:
        return len(self.demand)

    @property
    def n_periods(self) -> int:
        return len(self.capacity)

    @staticmethod
    def random(n_items: int, n_periods: int, rng: Random, tightness: float = 0.75) -> "CLSPInstance":
        demand = tuple(
            tuple(float(rng.choice([0, 0, rng.randint(10, 60)])) for _ in range(n_periods))
            for _ in range(n_items)
        )
        setup_cost = tuple(float(rng.randint(50, 300)) for _ in range(n_items))
        holding_cost = tuple(float(rng.randint(1, 5)) for _ in range(n_items))
        setup_time = tuple(float(rng.randint(2, 8)) for _ in range(n_items))
        # Capacidad uniforme tal que la capacidad acumulada cubra la demanda
        # acumulada (más un setup por ítem y período) en todo prefijo de
        # períodos: garantiza que exista un plan sin faltantes. `tightness`
        # < 1 la afloja; = 1 la deja justa.
        per_period_demand = [sum(demand[i][t] for i in range(n_items)) for t in range(n_periods)]
        cum, needed = 0.0, 0.0
        for t in range(n_periods):
            cum += per_period_demand[t]
            needed = max(needed, (cum + sum(setup_time) * (t + 1)) / (t + 1))
        cap = needed / tightness
        return CLSPInstance(demand, setup_cost, holding_cost, setup_time, tuple(cap for _ in range(n_periods)))

    @staticmethod
    def trigeiro(
        n_items: int,
        n_periods: int,
        rng: Random,
        utilization: float = 0.9,
        tbo: float = 2.0,
        demand_cv: float = 0.35,
        setup_time_share: float = 0.15,
        mean_demand: float = 100.0,
    ) -> "CLSPInstance":
        """Generador al estilo Trigeiro, Thomas & McClain (1989).

        - Demanda ~ Normal(mean_demand, cv·mean) truncada en 0; ~20% de ceros
          para dar estructura "lumpy".
        - Costo de setup derivado de un TBO (time-between-orders) objetivo vía
          EOQ: s_i = tbo² · h_i · d̄_i / 2. TBO alto ⇒ pocos setups grandes.
        - Tiempo de setup como fracción de la capacidad por período
          (`setup_time_share` repartido entre ítems).
        - Capacidad uniforme tal que la utilización media (demanda + un setup
          por ítem y período) sea `utilization`; luego se ajusta al mínimo que
          garantiza factibilidad por prefijo, para no generar faltantes
          inevitables. Utilización 0.9–0.98 es lo que endurece la instancia.
        """
        demand_rows = []
        for _ in range(n_items):
            row = []
            for _ in range(n_periods):
                if rng.random() < 0.2:
                    row.append(0.0)
                else:
                    row.append(max(0.0, round(rng.gauss(mean_demand, demand_cv * mean_demand))))
            demand_rows.append(tuple(row))
        demand = tuple(demand_rows)
        holding_cost = tuple(float(rng.choice([1, 2, 3, 4, 5])) for _ in range(n_items))
        mean_d = [sum(row) / n_periods for row in demand]
        setup_cost = tuple(round(tbo**2 * holding_cost[i] * max(mean_d[i], 1.0) / 2) for i in range(n_items))

        per_period_demand = [sum(demand[i][t] for i in range(n_items)) for t in range(n_periods)]
        avg_load = sum(per_period_demand) / n_periods
        # cap · util = avg_load + total_setup_time ; total_setup_time = share · cap
        cap = avg_load / (utilization - setup_time_share)
        total_setup_time = setup_time_share * cap
        setup_time = tuple(round(total_setup_time / n_items, 1) for _ in range(n_items))

        cum, needed = 0.0, 0.0
        for t in range(n_periods):
            cum += per_period_demand[t]
            needed = max(needed, (cum + sum(setup_time) * (t + 1)) / (t + 1))
        cap = max(cap, needed * 1.01)
        return CLSPInstance(demand, setup_cost, holding_cost, setup_time, tuple(round(cap) for _ in range(n_periods)))

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(f"{self.n_items} {self.n_periods}\n")
            f.write(" ".join(str(c) for c in self.capacity) + "\n")
            for i in range(self.n_items):
                f.write(f"{self.setup_cost[i]} {self.holding_cost[i]} {self.setup_time[i]}\n")
                f.write(" ".join(str(d) for d in self.demand[i]) + "\n")

    @staticmethod
    def load(path: str) -> "CLSPInstance":
        with open(path) as f:
            n_items, n_periods = map(int, f.readline().split())
            capacity = tuple(float(c) for c in f.readline().split())
            setup_cost, holding_cost, setup_time, demand = [], [], [], []
            for _ in range(n_items):
                s, h, st = map(float, f.readline().split())
                setup_cost.append(s)
                holding_cost.append(h)
                setup_time.append(st)
                demand.append(tuple(float(d) for d in f.readline().split()))
        assert len(capacity) == n_periods
        return CLSPInstance(tuple(demand), tuple(setup_cost), tuple(holding_cost), tuple(setup_time), capacity)


def var_name(i: int, t: int) -> str:
    return f"y_{i}_{t}"


class CLSPMip:
    """Modelo MIP del CLSP con interfaz `core.mip.MIPModel` (fijar / entera / relajar)."""

    def __init__(self, inst: CLSPInstance):
        self.inst = inst
        self._names = [var_name(i, t) for i in range(inst.n_items) for t in range(inst.n_periods)]
        self.last_objective: float | None = None
        self.penalty = shortage_penalty(inst)

    def variables(self) -> list[str]:
        return list(self._names)

    def _build(self, fixed: dict[str, float], integer: set[str], relaxed: set[str]):
        inst = self.inst
        prob = pulp.LpProblem("clsp", pulp.LpMinimize)
        y, x, s, u = {}, {}, {}, {}
        for i in range(inst.n_items):
            big_m = sum(inst.demand[i])
            for t in range(inst.n_periods):
                name = var_name(i, t)
                if name in fixed:
                    v = int(round(fixed[name]))
                    y[i, t] = pulp.LpVariable(name, lowBound=v, upBound=v, cat="Continuous")
                elif name in relaxed:
                    y[i, t] = pulp.LpVariable(name, lowBound=0, upBound=1, cat="Continuous")
                else:
                    y[i, t] = pulp.LpVariable(name, cat="Binary")
                x[i, t] = pulp.LpVariable(f"x_{i}_{t}", lowBound=0)
                s[i, t] = pulp.LpVariable(f"s_{i}_{t}", lowBound=0)
                u[i, t] = pulp.LpVariable(f"u_{i}_{t}", lowBound=0)
                prob += x[i, t] <= big_m * y[i, t]
                prev = s[i, t - 1] if t > 0 else 0
                # balance con faltante (lost sales) u
                prob += prev + x[i, t] + u[i, t] - s[i, t] == inst.demand[i][t]
        for t in range(inst.n_periods):
            prob += (
                pulp.lpSum(x[i, t] + inst.setup_time[i] * y[i, t] for i in range(inst.n_items))
                <= inst.capacity[t]
            )
        prob += pulp.lpSum(
            inst.setup_cost[i] * y[i, t] + inst.holding_cost[i] * s[i, t] + self.penalty * u[i, t]
            for i in range(inst.n_items)
            for t in range(inst.n_periods)
        )
        return prob, y, u

    def solve(self, fixed, integer, relaxed, time_limit, warm_start=None, near=None):
        prob, y, _u = self._build(fixed, integer, relaxed)
        if near is not None:
            x_bar, k = near
            prob += (
                pulp.lpSum(
                    (1 - y[i, t]) if round(x_bar.get(var_name(i, t), 0.0)) >= 1 else y[i, t]
                    for (i, t) in y
                    if var_name(i, t) not in fixed
                )
                <= k
            )
        if warm_start:
            for (i, t), v in y.items():
                if v.cat == "Binary" and var_name(i, t) in warm_start:
                    v.setInitialValue(int(round(warm_start[var_name(i, t)])))
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=max(1, int(round(time_limit))), warmStart=bool(warm_start))
        prob.solve(solver)
        self.last_objective = None
        if pulp.LpStatus[prob.status] not in ("Optimal", "Not Solved"):
            return None
        vals = {var_name(i, t): v.value() for (i, t), v in y.items()}
        if any(val is None for val in vals.values()):
            return None
        self.last_objective = float(pulp.value(prob.objective))
        return {k: float(round(v)) if k not in relaxed else float(v) for k, v in vals.items()}

    def evaluate_setups(self, sol: Solution) -> tuple[float, float]:
        """LP con todos los setups fijos. Retorna (costo, faltante_total)."""
        fixed = {var_name(i, t): float(sol[i][t]) for i in range(self.inst.n_items) for t in range(self.inst.n_periods)}
        prob, _y, u = self._build(fixed, set(), set())
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        shortage = sum(v.value() or 0.0 for v in u.values())
        return float(pulp.value(prob.objective)), shortage


class LotSizingModel:
    """Implementa `core.contracts.ProblemModel` para una instancia fija."""

    def __init__(self, inst: CLSPInstance):
        self.inst = inst
        self.mip = CLSPMip(inst)
        self._cache: dict[Solution, tuple[float, float]] = {}
        self.evaluations = 0

    def load(self, path: str) -> CLSPInstance:
        return CLSPInstance.load(path)

    def _eval(self, sol: Solution) -> tuple[float, float]:
        if sol not in self._cache:
            self._cache[sol] = self.mip.evaluate_setups(sol)
            self.evaluations += 1
        return self._cache[sol]

    def objective(self, sol: Solution) -> float:
        return self._eval(sol)[0]

    def is_feasible(self, sol: Solution) -> bool:
        return self._eval(sol)[1] < 1e-6

    def build_mip(self, inst: CLSPInstance) -> CLSPMip:
        return self.mip

    def to_assignment(self, sol: Solution) -> dict[str, float]:
        return {var_name(i, t): float(sol[i][t]) for i in range(self.inst.n_items) for t in range(self.inst.n_periods)}

    def from_assignment(self, x: dict[str, float]) -> Solution:
        return tuple(
            tuple(x[var_name(i, t)] >= 0.5 for t in range(self.inst.n_periods)) for i in range(self.inst.n_items)
        )

    def variable_groups(self, inst: CLSPInstance) -> dict[str, list[str]]:
        return {f"t{t}": [var_name(i, t) for i in range(inst.n_items)] for t in range(inst.n_periods)}
