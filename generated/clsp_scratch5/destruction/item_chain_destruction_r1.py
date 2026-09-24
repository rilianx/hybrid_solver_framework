from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "item_chain_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "span_factor": {"type": "float", "range": [0.5, 2.5]},
    },
}


class ItemChainDestruction:
    """Libera cadenas temporales completas de uno o varios ítems, rompiendo su patrón de setups."""

    def __init__(self, problem, inst, span_factor: float = 1.2):
        self.problem = problem
        self.inst = inst
        self.span_factor = span_factor

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        all_vars = [var_name(i, t) for i in range(n_items) for t in range(n_periods)]
        k = max(1, int(round(ratio * len(all_vars))))

        # Escogemos ítems con muchos setups activos o patrones fragmentados.
        item_scores = []
        for i in range(n_items):
            active = [t for t in range(n_periods) if sol[i][t]]
            count = len(active)
            if count == 0:
                score = 0.0
            else:
                gaps = 0
                for a, b in zip(active, active[1:]):
                    if b > a + 1:
                        gaps += b - a - 1
                score = count + 0.25 * gaps + self.span_factor * rng.random()
            item_scores.append((score, i, active))

        item_scores.sort(reverse=True)

        free_vars: set[str] = set()
        for _, i, active in item_scores:
            if not active:
                continue
            # Liberamos una cadena temporal alrededor de los setups del ítem seleccionado.
            start = max(0, min(active) - rng.randint(0, 1))
            end = min(n_periods - 1, max(active) + rng.randint(0, 1))
            for t in range(start, end + 1):
                free_vars.add(var_name(i, t))
                if len(free_vars) >= k:
                    break
            if len(free_vars) >= k:
                break

        # Si no alcanza, añadimos setups activos de otros ítems para completar.
        if len(free_vars) < k:
            active_vars = [var_name(i, t) for i in range(n_items) for t in range(n_periods) if sol[i][t] and var_name(i, t) not in free_vars]
            rng.shuffle(active_vars)
            for v in active_vars:
                free_vars.add(v)
                if len(free_vars) >= k:
                    break

        # Garantía mínima.
        if not free_vars:
            free_vars.add(rng.choice(all_vars))

        if len(free_vars) > k:
            free_vars = set(rng.sample(sorted(free_vars), k))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2, span_factor: float = 1.2):
    return ItemChainDestruction(problem, problem.inst, span_factor=span_factor)
