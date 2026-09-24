from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "setup_poco_efectivo",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
    },
}


class SetupPocoEfectivoDestruction:
    """Libera setups localmente débiles: pequeños, aislados o con poca demanda futura cubierta."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst
        self._groups = problem.variable_groups(inst)

    def _setup_score(self, sol, i: int, t: int) -> float:
        inst = self.inst
        n_periods = inst.n_periods

        # Demanda del ítem en el período actual y demanda futura hasta el próximo setup.
        local_demand = inst.demand[i][t]
        next_t = None
        for tt in range(t + 1, n_periods):
            if sol[i][tt]:
                next_t = tt
                break
        end = next_t if next_t is not None else n_periods
        covered_demand = sum(inst.demand[i][tt] for tt in range(t, end))

        # Aislamiento: setups muy separados suelen ser candidatos a fusionarse o moverse.
        prev_gap = t
        for tt in range(t - 1, -1, -1):
            if sol[i][tt]:
                prev_gap = t - tt
                break
        next_gap = n_periods - 1 - t
        if next_t is not None:
            next_gap = next_t - t

        # Menor score => setup más débil.
        # Penalizamos poco valor marginal: poca demanda local/futura, y cercanía de setups.
        demand_term = 1.0 / (1.0 + local_demand + 0.25 * covered_demand)
        cover_term = 1.0 / (1.0 + covered_demand)
        isolation_term = 1.0 / (1.0 + min(prev_gap, next_gap))
        sparse_term = 1.0 if covered_demand <= 1e-9 else min(1.0, local_demand / covered_demand)

        return 0.45 * demand_term + 0.35 * cover_term + 0.15 * isolation_term + 0.05 * sparse_term

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)

        on_vars = []
        for i in range(self.inst.n_items):
            for t in range(self.inst.n_periods):
                if sol[i][t]:
                    on_vars.append((self._setup_score(sol, i, t), i, t))

        all_vars = set(assignment.keys())
        if not on_vars:
            # Fallback seguro: liberar una variable cualquiera.
            chosen_name = next(iter(all_vars))
            free_vars = {chosen_name}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        k = max(1, int(round(ratio * len(on_vars))))
        on_vars.sort(key=lambda x: x[0])

        # Tomamos un conjunto candidato de setups débiles y añadimos un poco de azar
        # para diversificar entre setups con score similar.
        pool_size = min(len(on_vars), max(k, 2 * k))
        pool = on_vars[:pool_size]
        rng.shuffle(pool)
        chosen = pool[:k]

        free_vars = {var_name(i, t) for _, i, t in chosen}
        if not free_vars:
            free_vars = {var_name(on_vars[0][1], on_vars[0][2])}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25):
    return SetupPocoEfectivoDestruction(problem, problem.inst)
