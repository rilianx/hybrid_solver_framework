from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "capacity_critical_period_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.7]}},
}


class CapacityCriticalPeriodDestruction:
    """Libera setups de los períodos más congestionados para que el LP redistribuya carga."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        period_load = []
        for t in range(n_periods):
            load = 0.0
            for i in range(n_items):
                if sol[i][t]:
                    load += self.inst.setup_time[i] + self.inst.demand[i][t]
            slack = self.inst.capacity[t] - load
            period_load.append((slack, t))

        # Periodos más tensos primero; en empate, preferir más setups activos.
        period_load.sort(key=lambda x: (x[0], x[1]))
        chosen_vars = []
        for _, t in period_load:
            active = [i for i in range(n_items) if sol[i][t]]
            rng.shuffle(active)
            for i in active:
                chosen_vars.append(var_name(i, t))
                if len(chosen_vars) >= k:
                    break
            if len(chosen_vars) >= k:
                break

        # Si faltan variables, completamos con setups cercanos en períodos vecinos.
        if len(chosen_vars) < k:
            for _, t in period_load:
                neighbors = []
                if t > 0:
                    neighbors.append(t - 1)
                if t + 1 < n_periods:
                    neighbors.append(t + 1)
                for tt in neighbors:
                    active = [i for i in range(n_items) if sol[i][tt]]
                    rng.shuffle(active)
                    for i in active:
                        name = var_name(i, tt)
                        if name not in chosen_vars:
                            chosen_vars.append(name)
                            if len(chosen_vars) >= k:
                                break
                    if len(chosen_vars) >= k:
                        break
                if len(chosen_vars) >= k:
                    break

        if not chosen_vars:
            chosen_vars.append(var_name(rng.randrange(n_items), rng.randrange(n_periods)))

        free_vars = set(chosen_vars)
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.22):
    return CapacityCriticalPeriodDestruction(problem, problem.inst)
