from __future__ import annotations

from random import Random


COMPONENT = {
    "name": "rolling_horizon_cover_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class RollingHorizonCoverConstructor:
    """Construcción greedy por horizonte rodante: abre setups solo cuando es necesario y
    reparte la demanda de cada ítem sobre los períodos con más capacidad residual."""

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods

        # Setups binarios
        y = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # Capacidad residual por período
        remaining_cap = [float(c) for c in inst.capacity]

        # Demanda total remanente por ítem
        remaining_demand = [float(sum(inst.demand[i])) for i in range(n_items)]

        # Procesar primero los ítems "más costosos" para reducir riesgo de setups innecesarios
        items = list(range(n_items))
        items.sort(
            key=lambda i: (
                sum(inst.demand[i]) > 0.0,
                inst.setup_cost[i],
                sum(inst.demand[i]),
                -inst.holding_cost[i],
            ),
            reverse=True,
        )

        for i in items:
            demand_i = remaining_demand[i]
            if demand_i <= 1e-12:
                continue

            setup_time_i = float(inst.setup_time[i])

            # Períodos con mayor capacidad residual primero; desempate aleatorio estable vía rng
            periods = list(range(n_periods))
            periods.sort(key=lambda t: (remaining_cap[t], -t), reverse=True)

            # Cubrimos la demanda del ítem repartiendo producción entre períodos.
            for t in periods:
                if demand_i <= 1e-12:
                    break

                cap_t = remaining_cap[t]
                if cap_t <= 1e-12:
                    continue

                # Si el setup no cabe en este período, no podemos usarlo para este ítem.
                if cap_t + 1e-12 < setup_time_i:
                    continue

                if not y[i][t]:
                    y[i][t] = True
                    cap_t -= setup_time_i

                if cap_t <= 1e-12:
                    remaining_cap[t] = cap_t
                    continue

                take = min(cap_t, demand_i)
                remaining_cap[t] -= take
                demand_i -= take

            remaining_demand[i] = demand_i

            # Reparación conservadora: si aún queda demanda, intentamos usar cualquier período con capacidad
            # residual suficiente para setup + algo de producción.
            if demand_i > 1e-12:
                periods = list(range(n_periods))
                periods.sort(key=lambda t: (remaining_cap[t], -t), reverse=True)
                for t in periods:
                    if demand_i <= 1e-12:
                        break
                    cap_t = remaining_cap[t]
                    if cap_t <= 1e-12 or cap_t + 1e-12 < setup_time_i:
                        continue
                    if not y[i][t]:
                        y[i][t] = True
                        cap_t -= setup_time_i
                    if cap_t <= 1e-12:
                        remaining_cap[t] = cap_t
                        continue
                    take = min(cap_t, demand_i)
                    remaining_cap[t] -= take
                    demand_i -= take
                remaining_demand[i] = demand_i

        # Si alguna demanda quedó sin cubrir por redondeos/empates, forzamos una última pasada.
        # Se intenta ubicarla donde más capacidad quede; si no existe capacidad suficiente, la solución
        # resultará infactible, pero esto solo ocurrirá si la instancia misma lo es.
        for i in range(n_items):
            demand_i = remaining_demand[i]
            if demand_i <= 1e-12:
                continue
            setup_time_i = float(inst.setup_time[i])
            for t in sorted(range(n_periods), key=lambda tt: (remaining_cap[tt], -tt), reverse=True):
                if demand_i <= 1e-12:
                    break
                if remaining_cap[t] + 1e-12 < setup_time_i:
                    continue
                if not y[i][t]:
                    y[i][t] = True
                    remaining_cap[t] -= setup_time_i
                take = min(remaining_cap[t], demand_i)
                if take > 1e-12:
                    remaining_cap[t] -= take
                    demand_i -= take
            remaining_demand[i] = demand_i

        return tuple(tuple(row) for row in y)


def build_component(problem, **params):
    return RollingHorizonCoverConstructor()
