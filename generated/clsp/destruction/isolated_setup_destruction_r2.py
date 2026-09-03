from random import Random

COMPONENT = {
    "name": "isolated_setup_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "lookahead": {"type": "int", "range": [1, 5]},
    },
}


class IsolatedSetupDestruction:
    """Libera setups por período completo en zonas de baja densidad de demanda.
    La idea es distinta a liberar setups aislados por ítem: aquí se destruyen
    patrones de un período entero para forzar reajustes temporales.
    """

    def __init__(self, problem, inst, lookahead: int = 2):
        self.problem = problem
        self.inst = inst
        self.lookahead = lookahead

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods

        target = max(1, int(round(ratio * n_items * n_periods)))
        free_vars = set()

        # Score por período: preferimos períodos con setups "aislados" respecto a demanda cercana.
        period_scores = []
        for t in range(n_periods):
            setups_t = [i for i in range(n_items) if sol[i][t]]
            if not setups_t:
                continue

            # Demanda cercana al período: si es baja, es más plausible reubicar la producción.
            left = max(0, t - self.lookahead)
            right = min(n_periods, t + self.lookahead + 1)
            nearby_demand = 0.0
            for i in range(n_items):
                nearby_demand += sum(self.inst.demand[i][tt] for tt in range(left, right))

            # Densidad de setups: más setups en el período => más candidato a ser destruido.
            setup_count = len(setups_t)

            # Menor score = más candidato.
            score = nearby_demand / max(1, setup_count)
            period_scores.append((score, t, setup_count))

        period_scores.sort(key=lambda x: (x[0], -x[2]))

        # Primero: liberar períodos completos con peor densidad.
        for _, t, _ in period_scores:
            for i in range(n_items):
                if sol[i][t]:
                    free_vars.add(f"y_{i}_{t}")
            if len(free_vars) >= target:
                break

        # Si aún faltan variables, completar con setups de períodos vecinos a los ya liberados,
        # priorizando períodos con poca demanda cercana.
        if len(free_vars) < target:
            selected_periods = {int(v.split("_")[-1]) for v in free_vars} if free_vars else set()
            candidate_vars = []
            for t in range(n_periods):
                if t in selected_periods:
                    continue
                # sólo setups activos
                active = [i for i in range(n_items) if sol[i][t]]
                if not active:
                    continue
                left = max(0, t - self.lookahead)
                right = min(n_periods, t + self.lookahead + 1)
                nearby_demand = 0.0
                for i in range(n_items):
                    nearby_demand += sum(self.inst.demand[i][tt] for tt in range(left, right))
                for i in active:
                    candidate_vars.append((nearby_demand, t, i))

            candidate_vars.sort(key=lambda x: x[0])
            for _, t, i in candidate_vars:
                free_vars.add(f"y_{i}_{t}")
                if len(free_vars) >= target:
                    break

        # Fallback aleatorio si la solución tiene pocos setups activos.
        if len(free_vars) < target:
            remaining = [
                f"y_{i}_{t}"
                for i in range(n_items)
                for t in range(n_periods)
                if sol[i][t] and f"y_{i}_{t}" not in free_vars
            ]
            rng.shuffle(remaining)
            for v in remaining:
                free_vars.add(v)
                if len(free_vars) >= target:
                    break

        if not free_vars and assignment:
            free_vars.add(next(iter(assignment.keys())))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, lookahead: int = 2):
    return IsolatedSetupDestruction(problem, problem.inst, lookahead=lookahead)
