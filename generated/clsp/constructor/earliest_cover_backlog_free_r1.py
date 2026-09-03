from random import Random
from typing import Any

COMPONENT = {
    "name": "earliest_cover_backlog_free",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "lookahead": {"type": "int", "range": [1, 12]},
        "frontload_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class EarliestCoverBacklogFree:
    """Constructor voraz: abre setups lo antes posible y agrupa demanda futura hasta que la carga estimada se acerca a la capacidad."""

    def __init__(self, lookahead: int = 4, frontload_bias: float = 0.35):
        self.lookahead = lookahead
        self.frontload_bias = frontload_bias

    @staticmethod
    def _empty_solution(n_items: int, n_periods: int):
        return tuple(tuple(False for _ in range(n_periods)) for _ in range(n_items))

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        demand = inst.demand
        setup_time = inst.setup_time
        capacity = inst.capacity

        sol = [list(row) for row in self._empty_solution(n_items, n_periods)]

        # Heurística: para cada ítem, agrupa demanda futura en bloques.
        # Se abre un setup cuando el bloque acumulado ya justifica el costo de mantener inventario
        # o cuando la capacidad del período actual parece suficiente para sostenerlo.
        for i in range(n_items):
            t = 0
            while t < n_periods:
                # Buscar la siguiente demanda positiva si estamos antes de ella.
                while t < n_periods and demand[i][t] <= 0:
                    t += 1
                if t >= n_periods:
                    break

                sol[i][t] = True

                # Mirada adelante: decidir hasta qué período "cubrir" con este setup.
                cover_until = t
                future = 0.0
                horizon = min(n_periods - 1, t + self.lookahead)
                for tt in range(t + 1, horizon + 1):
                    future += demand[i][tt]
                    # Coste inventario acumulado aproximado: cuanto más lejos, más penaliza.
                    hold_penalty = inst.holding_cost[i] * future * (tt - t)
                    setup_saving = inst.setup_cost[i]
                    cap_margin = capacity[tt] - setup_time[i]
                    if future > 0 and (hold_penalty <= setup_saving * (0.5 + self.frontload_bias) or cap_margin >= future):
                        cover_until = tt
                    else:
                        break

                # Avanzar hasta el siguiente período no cubierto.
                t = cover_until + 1

        return tuple(tuple(row) for row in sol)


def build_component(problem, lookahead: int = 4, frontload_bias: float = 0.35):
    return EarliestCoverBacklogFree(lookahead=lookahead, frontload_bias=frontload_bias)
