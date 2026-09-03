from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "adjacent_pair_merge_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class AdjacentPairMergeDestruction:
    """Libera parejas de setups consecutivos del mismo ítem para favorecer fusiones y stock."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        pairs = []
        for i in range(n_items):
            t = 0
            while t < n_periods - 1:
                if sol[i][t] and sol[i][t + 1]:
                    # Preferimos pares con mayor costo de setup y mayor costo de inventario:
                    # liberar ambos permite al LP decidir una sola reubicación más barata.
                    score = self.inst.setup_cost[i] + self.inst.holding_cost[i]
                    pairs.append((score, i, t))
                    t += 2
                else:
                    t += 1

        pairs.sort(reverse=True)

        free_vars = set()
        for _, i, t in pairs:
            free_vars.add(var_name(i, t))
            free_vars.add(var_name(i, t + 1))
            if len(free_vars) >= k:
                break

        # Si no encontramos pares consecutivos, caemos a setups aislados con preferencia por ítems caros.
        if len(free_vars) < 1:
            singletons = []
            for i in range(n_items):
                for t in range(n_periods):
                    if sol[i][t]:
                        singletons.append((self.inst.setup_cost[i], i, t))
            singletons.sort(reverse=True)
            for _, i, t in singletons:
                free_vars.add(var_name(i, t))
                if len(free_vars) >= 1:
                    break

        if not free_vars:
            free_vars.add(var_name(0, 0))

        # Completamos al azar con setups activos restantes hasta alcanzar el tamaño deseado.
        if len(free_vars) < k:
            candidates = [
                var_name(i, t)
                for i in range(n_items)
                for t in range(n_periods)
                if sol[i][t] and var_name(i, t) not in free_vars
            ]
            rng.shuffle(candidates)
            for name in candidates:
                free_vars.add(name)
                if len(free_vars) >= k:
                    break

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.18):
    return AdjacentPairMergeDestruction(problem, problem.inst)
