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
    """Constructor que reparte setups para cubrir cada prefijo de demanda con capacidad suficiente."""

    def __init__(self, window: int = 4, shift_prob: float = 0.7, prefer_early: bool = True):
        self.window = window
        self.shift_prob = shift_prob
        self.prefer_early = prefer_early

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods

        demand_sum = [0.0] * n_items
        cum_demand = [[0.0] * n_periods for _ in range(n_items)]
        first_demand = [None] * n_items
        last_demand = [None] * n_items

        for i in range(n_items):
            acc = 0.0
            for t in range(n_periods):
                d = float(inst.demand[i][t])
                acc += d
                cum_demand[i][t] = acc
                demand_sum[i] += d
                if d > 1e-12:
                    if first_demand[i] is None:
                        first_demand[i] = t
                    last_demand[i] = t

        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]
        remaining_cap = [float(inst.capacity[t]) for t in range(n_periods)]

        items = [i for i in range(n_items) if demand_sum[i] > 1e-12]
        items.sort(key=lambda i: (first_demand[i] if first_demand[i] is not None else n_periods, -demand_sum[i], i))

        for i in items:
            ld = last_demand[i]
            if ld is None:
                continue

            available = 0.0

            for t in range(ld + 1):
                # Asegurar cobertura del prefijo t.
                needed = cum_demand[i][t]
                while available + 1e-12 < needed:
                    chosen = None

                    # Preferir el propio período t si está libre y cabe.
                    if not sol[i][t] and remaining_cap[t] >= inst.setup_time[i] - 1e-12:
                        chosen = t
                    else:
                        # Buscar un período previo libre con capacidad, priorizando temprano o tarde según parámetro.
                        if self.prefer_early:
                            period_range = range(0, t + 1)
                        else:
                            period_range = range(t, -1, -1)

                        for s in period_range:
                            if not sol[i][s] and remaining_cap[s] >= inst.setup_time[i] - 1e-12:
                                chosen = s
                                break

                    if chosen is None:
                        # Fallback: cualquier período no posterior al prefijo y con capacidad.
                        for s in range(0, t + 1):
                            if not sol[i][s] and remaining_cap[s] >= inst.setup_time[i] - 1e-12:
                                chosen = s
                                break

                    if chosen is None:
                        # No debería ocurrir en instancias factibles; dejamos de intentar este ítem.
                        break

                    sol[i][chosen] = True
                    remaining_cap[chosen] -= float(inst.setup_time[i])
                    available += max(0.0, float(inst.capacity[chosen]) - float(inst.setup_time[i]))

            # Verificación/recuperación final: si aún falta capacidad acumulada hasta el último período de demanda,
            # añadimos setups previos adicionales.
            total_available = 0.0
            for t in range(ld + 1):
                if sol[i][t]:
                    total_available += max(0.0, float(inst.capacity[t]) - float(inst.setup_time[i]))

            if total_available + 1e-12 < demand_sum[i]:
                for t in range(ld, -1, -1):
                    if total_available + 1e-12 >= demand_sum[i]:
                        break
                    if sol[i][t]:
                        continue
                    if remaining_cap[t] < float(inst.setup_time[i]) - 1e-12:
                        continue
                    sol[i][t] = True
                    remaining_cap[t] -= float(inst.setup_time[i])
                    total_available += max(0.0, float(inst.capacity[t]) - float(inst.setup_time[i]))

        return tuple(tuple(row) for row in sol)


def build_component(problem, window: int = 4, shift_prob: float = 0.7, prefer_early: bool = True):
    return SaturationBalancingShift(window=window, shift_prob=shift_prob, prefer_early=prefer_early)
