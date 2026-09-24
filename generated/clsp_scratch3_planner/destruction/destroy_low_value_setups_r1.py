from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "destroy_low_value_setups",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
    },
}


class DestroyLowValueSetups:
    """Libera setups con peor utilidad local: poca demanda futura cubierta vs. costo setup+inventario."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = inst.n_items, inst.n_periods

        # Número de setups a liberar, acotado por el tamaño total de la vista MIP.
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        # Precomputa demanda futura acumulada por ítem desde cada período t.
        future_demand = [
            [0.0] * (n_periods + 1) for _ in range(n_items)
        ]
        for i in range(n_items):
            acc = 0.0
            future_demand[i][n_periods] = 0.0
            for t in range(n_periods - 1, -1, -1):
                acc += float(inst.demand[i][t])
                future_demand[i][t] = acc

        # Precomputa demanda total futura del sistema por período (para bonus de utilidad).
        total_future_demand = [0.0] * n_periods
        acc_total = 0.0
        for t in range(n_periods - 1, -1, -1):
            acc_total += sum(float(inst.demand[i][t]) for i in range(n_items))
            total_future_demand[t] = acc_total

        # Inventario proxy: demanda del ítem en períodos intermedios entre t y futuras demandas
        # (cuanto más adelantado, más caro).
        candidates = []
        for i in range(n_items):
            s_cost = float(inst.setup_cost[i])
            h_cost = float(inst.holding_cost[i])
            for t in range(n_periods):
                if not sol[i][t]:
                    continue

                # Demanda futura del propio ítem que este setup puede cubrir.
                own_future = future_demand[i][t]
                if own_future <= 0.0:
                    # Setup aislado o inútil: muy bajo valor.
                    score = -s_cost
                    candidates.append((score, i, t))
                    continue

                # Approx. unidades que, en promedio, este setup "habilita" hasta el final.
                # Se premia cubrir demanda futura, pero se penaliza adelantar demasiado.
                periods_ahead = n_periods - t - 1
                avg_wait = 0.5 * periods_ahead  # proxy simple de inventario medio

                holding_penalty = h_cost * own_future * avg_wait

                # Bonus: si después de t hay mucha demanda total, el setup probablemente
                # evita consolidar demasiado tarde; si casi no hay demanda futura, es prescindible.
                system_pressure = total_future_demand[t] / max(1.0, n_periods - t)

                # Utilidad local: demanda futura cubierta por costo total.
                # Mayor score => mejor setup; queremos liberar los peores.
                score = (own_future + 0.1 * system_pressure) / (1.0 + s_cost + holding_penalty)

                # Penaliza setups que no son necesarios para cubrir su propia demanda futura,
                # o que parecen anticipados frente al patrón de demanda.
                if future_demand[i][t + 1] <= 1e-9:
                    score *= 0.25

                candidates.append((score, i, t))

        # Ordenar de peor a mejor utilidad; desempate aleatorio leve para diversificar.
        candidates.sort(key=lambda x: (x[0], rng.random()))

        chosen: set[tuple[int, int]] = set()
        for _, i, t in candidates:
            if len(chosen) >= k:
                break
            chosen.add((i, t))

        # Si por alguna razón no alcanzamos k (p.ej. pocas activaciones), añadimos setups aleatorios.
        if len(chosen) < k:
            all_active = [(i, t) for i in range(n_items) for t in range(n_periods) if sol[i][t]]
            rng.shuffle(all_active)
            for pair in all_active:
                if len(chosen) >= k:
                    break
                chosen.add(pair)

        # Garantiza al menos una variable liberada.
        if not chosen:
            for i in range(n_items):
                for t in range(n_periods):
                    if sol[i][t]:
                        chosen.add((i, t))
                        break
                if chosen:
                    break
        if not chosen:
            chosen.add((0, 0))

        free_vars = {var_name(i, t) for (i, t) in chosen}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25):
    return DestroyLowValueSetups(problem, problem.inst)
