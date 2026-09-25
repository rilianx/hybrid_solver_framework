from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "critical_period_seeding",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "priority_mode": {"type": "cat", "values": ["criticality", "holding", "demand"]},
        "use_rng_shuffle": {"type": "bool", "range": [0, 1]},
    },
}


class CriticalPeriodSeedingConstructor:
    """Constructor por siembra en períodos críticos y retroceso de lotes.

    Idea:
    1) Estima períodos tensos por demanda acumulada + tiempos de setup.
    2) Ordena ítems para reservar capacidad escasa a los más "críticos".
    3) Construye lotes hacia atrás: cada lote se fija en el último período
       con capacidad residual suficiente para cubrir un bloque de demanda.
    """

    def __init__(self, problem: Any, priority_mode: str = "criticality", use_rng_shuffle: bool = True):
        self.problem = problem
        self.inst = problem.inst
        self.priority_mode = priority_mode
        self.use_rng_shuffle = use_rng_shuffle

    def _period_pressure(self) -> list[float]:
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        total_dem = [sum(inst.demand[i][t] for i in range(n_items)) for t in range(n_periods)]
        cum_dem = 0.0
        cum_cap = 0.0
        pressure = []
        min_setup = sum(inst.setup_time)
        for t in range(n_periods):
            cum_dem += total_dem[t]
            cum_cap += inst.capacity[t]
            # presión acumulada: demanda + setup mínimos vs capacidad acumulada
            pressure.append((cum_dem + min_setup * (t + 1)) / max(cum_cap, 1e-9))
        return pressure

    def _item_key(self, i: int, pressure: list[float]) -> tuple[float, float, float]:
        inst = self.inst
        demand_sum = sum(inst.demand[i])
        weighted = sum((t + 1) * inst.demand[i][t] for t in range(inst.n_periods))
        setup_penalty = inst.setup_time[i] * inst.setup_cost[i]
        if self.priority_mode == "holding":
            return (inst.holding_cost[i], demand_sum, weighted)
        if self.priority_mode == "demand":
            return (demand_sum, weighted, setup_penalty)
        # criticality: items with late demand on critical periods first
        crit_score = sum(inst.demand[i][t] * pressure[t] for t in range(inst.n_periods))
        return (crit_score, setup_penalty, weighted)

    def _build_once(self, rng: Random, reverse: bool = False):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        pressure = self._period_pressure()

        order = list(range(n_items))
        order.sort(key=lambda i: self._item_key(i, pressure), reverse=True)
        if self.use_rng_shuffle:
            # Pequeña perturbación determinista por semilla, sin perder el orden base.
            block = max(2, n_items // 5)
            for start in range(0, n_items, block):
                chunk = order[start : start + block]
                rng.shuffle(chunk)
                order[start : start + block] = chunk
        if reverse:
            order.reverse()

        # Residual de capacidad por período.
        rem = [float(inst.capacity[t]) for t in range(n_periods)]
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # Procesa cada ítem construyendo lotes hacia atrás.
        for i in order:
            demands = inst.demand[i]
            if sum(demands) <= 1e-12:
                continue

            t = n_periods - 1
            while t >= 0:
                # Buscar el último período p <= t con capacidad suficiente
                # para cubrir un bloque de demanda que termine en t.
                block = 0.0
                chosen_p = -1
                chosen_block = 0.0
                for p in range(t, -1, -1):
                    block += demands[p]
                    need = block + inst.setup_time[i]
                    if rem[p] + 1e-9 >= need:
                        chosen_p = p
                        chosen_block = block
                        break

                if chosen_p >= 0:
                    sol[i][chosen_p] = True
                    rem[chosen_p] -= chosen_block + inst.setup_time[i]
                    t = chosen_p - 1
                else:
                    # Si no cabe ningún bloque terminando en t, agregamos más demanda
                    # hacia atrás hasta encontrar un período con holgura.
                    # En instancias factibles esto debería resolverse pronto.
                    t -= 1

        return tuple(tuple(row) for row in sol)

    def build(self, inst, rng: Random):
        # Construcción principal y dos reparaciones ligeras deterministas.
        cand = self._build_once(rng, reverse=False)
        if not self.problem.is_feasible(cand):
            cand2 = self._build_once(rng, reverse=True)
            if self.problem.is_feasible(cand2):
                cand = cand2
            else:
                # Repara añadiendo setups donde falten bloques: prueba una estrategia más
                # conservadora con todos los períodos en los que haya demanda.
                n_items, n_periods = inst.n_items, inst.n_periods
                rem = [float(inst.capacity[t]) for t in range(n_periods)]
                sol = [[False for _ in range(n_periods)] for _ in range(n_items)]
                for i in range(n_items):
                    # Una única partición por item: último período factible para cada prefijo.
                    t = n_periods - 1
                    while t >= 0:
                        if sum(inst.demand[i][: t + 1]) <= 1e-12:
                            t -= 1
                            continue
                        block = 0.0
                        chosen_p = -1
                        for p in range(t, -1, -1):
                            block += inst.demand[i][p]
                            need = block + inst.setup_time[i]
                            if rem[p] + 1e-9 >= need:
                                chosen_p = p
                                break
                        if chosen_p < 0:
                            # último recurso: colocar el setup en el primer período con más rem
                            chosen_p = max(range(t + 1), key=lambda p: rem[p])
                            block = sum(inst.demand[i][: t + 1])
                        sol[i][chosen_p] = True
                        rem[chosen_p] -= block + inst.setup_time[i]
                        t = chosen_p - 1
                cand = tuple(tuple(row) for row in sol)

        if not self.problem.is_feasible(cand):
            # Reparación final muy conservadora: abre setup en todos los períodos
            # necesarios por ítem con demanda. Es rara vez necesario, pero garantiza
            # un último intento determinista.
            sol = []
            for i in range(inst.n_items):
                row = []
                active = False
                for t in range(inst.n_periods):
                    if inst.demand[i][t] > 0 and not active:
                        row.append(True)
                        active = True
                    elif inst.demand[i][t] == 0 and active:
                        row.append(False)
                    else:
                        row.append(False)
                sol.append(tuple(row))
            cand = tuple(sol)
            # Si todavía no es factible, devolvemos el mejor intento; el validador
            # lo detectará. En instancias estándar no debería ocurrir.
            if not self.problem.is_feasible(cand):
                return cand

        return cand


def build_component(problem, priority_mode: str = "criticality", use_rng_shuffle: bool = True):
    return CriticalPeriodSeedingConstructor(
        problem=problem,
        priority_mode=priority_mode,
        use_rng_shuffle=use_rng_shuffle,
    )
