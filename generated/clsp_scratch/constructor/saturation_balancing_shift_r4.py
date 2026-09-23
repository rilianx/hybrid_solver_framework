from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "saturation_balancing_shift",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "window": {"type": "int", "range": [1, 12]},
        "shift_prob": {"type": "float", "range": [0.0, 1.0]},
        "prefer_early": {"type": "bool", "range": [0, 1]},
    },
}


class SaturationBalancingShift:
    """Constructor que reparte setups desde períodos saturados hacia períodos vecinos con holgura."""

    def __init__(self, window: int = 4, shift_prob: float = 0.7, prefer_early: bool = True):
        self.window = window
        self.shift_prob = shift_prob
        self.prefer_early = prefer_early

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods

        demand_sum = [sum(inst.demand[i][t] for t in range(n_periods)) for i in range(n_items)]
        first_demand = [None] * n_items
        last_demand = [None] * n_items
        cum_demand = [[0.0] * n_periods for _ in range(n_items)]
        for i in range(n_items):
            acc = 0.0
            for t in range(n_periods):
                acc += inst.demand[i][t]
                cum_demand[i][t] = acc
                if inst.demand[i][t] > 1e-12:
                    if first_demand[i] is None:
                        first_demand[i] = t
                    last_demand[i] = t

        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]
        remaining_cap = [float(inst.capacity[t]) for t in range(n_periods)]

        items = [i for i in range(n_items) if demand_sum[i] > 1e-12]
        items.sort(key=lambda i: (first_demand[i] if first_demand[i] is not None else n_periods, -demand_sum[i], i))

        # Fase 1: construir un patrón factible de setups por prefijos de demanda.
        for i in items:
            if first_demand[i] is None:
                continue

            available = 0.0
            for t in range(n_periods):
                if not sol[i][t] and t <= last_demand[i]:
                    pass

                # Asegura cobertura del prefijo t: si falta capacidad, añade setups en t o antes.
                if t > last_demand[i]:
                    break

                while available + 1e-12 < cum_demand[i][t]:
                    chosen = None

                    # Preferir el período actual si cabe, para mantener la idea de saturación.
                    if not sol[i][t] and remaining_cap[t] >= inst.setup_time[i] - 1e-12:
                        chosen = t
                    else:
                        # Buscar el último período previo con capacidad residual.
                        for s in range(t, -1, -1):
                            if not sol[i][s] and remaining_cap[s] >= inst.setup_time[i] - 1e-12:
                                chosen = s
                                break

                    if chosen is None:
                        # Si no hay hueco previo, intentar expandir con cualquier período no posterior al prefijo.
                        # Se recorre de forma determinista, priorizando períodos tempranos si se pide.
                        period_range = range(0, t + 1) if self.prefer_early else range(t, -1, -1)
                        for s in period_range:
                            if not sol[i][s] and remaining_cap[s] >= inst.setup_time[i] - 1e-12:
                                chosen = s
                                break

                    if chosen is None:
                        # Fallback muy conservador: escoger el mejor período aún libre con capacidad,
                        # siempre no posterior al último período con demanda.
                        for s in range(0, last_demand[i] + 1):
                            if not sol[i][s] and remaining_cap[s] >= inst.setup_time[i] - 1e-12:
                                chosen = s
                                break

                    if chosen is None:
                        # No debería ocurrir en instancias factibles, pero evitamos devolver algo infactible.
                        break

                    sol[i][chosen] = True
                    remaining_cap[chosen] -= inst.setup_time[i]
                    available += max(0.0, inst.capacity[chosen] - inst.setup_time[i])

        # Fase 2: reparar cualquier déficit residual añadiendo setups previos al último período demandado.
        for i in items:
            if last_demand[i] is None:
                continue
            current_avail = 0.0
            setups = [t for t in range(n_periods) if sol[i][t]]
            for t in range(n_periods):
                if sol[i][t]:
                    current_avail += max(0.0, inst.capacity[t] - inst.setup_time[i])

            if current_avail + 1e-12 >= demand_sum[i]:
                continue

            for t in range(last_demand[i], -1, -1):
                if current_avail + 1e-12 >= demand_sum[i]:
                    break
                if sol[i][t]:
                    continue
                if remaining_cap[t] < inst.setup_time[i] - 1e-12:
                    continue
                sol[i][t] = True
                remaining_cap[t] -= inst.setup_time[i]
                current_avail += max(0.0, inst.capacity[t] - inst.setup_time[i])

        # Fase 3: corrimiento local de setups a períodos con más holgura, sin perder factibilidad.
        loads = [sum(inst.setup_time[i] for i in range(n_items) if sol[i][t]) for t in range(n_periods)]
        for i in range(n_items):
            if demand_sum[i] <= 1e-12:
                continue
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                if first_demand[i] is not None and t <= first_demand[i]:
                    continue
                if rng.random() > self.shift_prob:
                    continue

                candidates = []
                for dt in range(-self.window, self.window + 1):
                    if dt == 0:
                        continue
                    tt = t + dt
                    if tt < 0 or tt >= n_periods:
                        continue
                    if remaining_cap[tt] + inst.setup_time[i] <= inst.capacity[tt] + 1e-12:
                        candidates.append(tt)

                if not candidates:
                    continue

                candidates.sort(key=lambda tt: (loads[tt], tt if self.prefer_early else -tt))
                best_tt = candidates[0]
                if loads[best_tt] + inst.setup_time[i] < loads[t] - 1e-12:
                    sol[i][t] = False
                    sol[i][best_tt] = True
                    loads[t] -= inst.setup_time[i]
                    loads[best_tt] += inst.setup_time[i]

        return tuple(tuple(row) for row in sol)


def build_component(problem, window: int = 4, shift_prob: float = 0.7, prefer_early: bool = True):
    return SaturationBalancingShift(window=window, shift_prob=shift_prob, prefer_early=prefer_early)
