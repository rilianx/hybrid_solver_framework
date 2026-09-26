"""Instancia del CLSP (lot sizing capacitado multi-ítem, un nivel, sin backlog).

Separada de `problem_model.py` para poder dársela al LLM que genera el `ProblemModel` sin
darle el modelo escrito a mano (`llm_spec.make_model_spec` prohíbe importar este último).
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random


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

    def to_text(self) -> str:
        """Formato de entrada: `n_items n_periods`, la capacidad por período y, por ítem, una línea
        `setup_cost holding_cost setup_time` seguida de su demanda por período."""
        lines = [f"{self.n_items} {self.n_periods}", " ".join(str(c) for c in self.capacity)]
        for i in range(self.n_items):
            lines += [f"{self.setup_cost[i]} {self.holding_cost[i]} {self.setup_time[i]}", " ".join(str(d) for d in self.demand[i])]
        return "\n".join(lines) + "\n"

    @staticmethod
    def parse(text: str) -> "CLSPInstance":
        rows = iter(line for line in text.splitlines() if line.strip())
        n_items, n_periods = map(int, next(rows).split())
        capacity = tuple(float(c) for c in next(rows).split())
        setup_cost, holding_cost, setup_time, demand = [], [], [], []
        for _ in range(n_items):
            s, h, st = map(float, next(rows).split())
            setup_cost.append(s)
            holding_cost.append(h)
            setup_time.append(st)
            demand.append(tuple(float(d) for d in next(rows).split()))
        assert len(capacity) == n_periods and all(len(d) == n_periods for d in demand)
        return CLSPInstance(tuple(demand), tuple(setup_cost), tuple(holding_cost), tuple(setup_time), capacity)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.to_text())

    @staticmethod
    def load(path: str) -> "CLSPInstance":
        with open(path) as f:
            return CLSPInstance.parse(f.read())
