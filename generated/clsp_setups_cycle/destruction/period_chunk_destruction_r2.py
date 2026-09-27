from random import Random
from typing import Any

COMPONENT = {
    "name": "period_chunk_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
        "window_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class PeriodChunkDestruction:
    """Libera bloques de períodos completos, favoreciendo ventanas contiguas de tiempo."""

    def __init__(self, problem, ratio: float, window_bias: float):
        self.problem = problem
        self.ratio = float(ratio)
        self.window_bias = float(window_bias)

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        if not assignment:
            return {}, set()

        inst = self.problem.inst
        n_periods = getattr(inst, "n_periods", 0)
        vars_ = list(assignment.keys())

        # Agrupa variables por período cuando el nombre lo permite; si no, usa el orden de aparición.
        period_to_vars: dict[int, list[str]] = {t: [] for t in range(max(0, n_periods))}
        unparsed: list[str] = []
        for v in vars_:
            parts = v.rsplit("_", 1)
            try:
                t = int(parts[-1])
            except (ValueError, TypeError):
                unparsed.append(v)
                continue
            if 0 <= t < n_periods:
                period_to_vars.setdefault(t, []).append(v)
            else:
                unparsed.append(v)

        # Número de períodos a liberar: crece monótonamente con ratio.
        if n_periods > 0:
            k = int(round(max(0.0, min(1.0, ratio)) * n_periods))
            k = max(1, min(n_periods, k))
            if k == n_periods:
                chosen_periods = set(range(n_periods))
            else:
                start = rng.randrange(0, n_periods - k + 1)
                chosen_periods = set(range(start, start + k))
            free_vars = {v for t in chosen_periods for v in period_to_vars.get(t, [])}
        else:
            # Fallback: destruye una fracción monotónica de las variables disponibles.
            target = max(1, min(len(vars_), int(round(max(0.0, min(1.0, ratio)) * len(vars_)))))
            free_vars = set(rng.sample(vars_, target))

        # Si todavía hay muy pocas variables liberadas, completa con variables no liberadas,
        # sin romper la monotonía con respecto a los períodos ya seleccionados.
        if n_periods > 0:
            target = max(len(free_vars), int(round(max(0.0, min(1.0, ratio)) * len(vars_))))
            if len(free_vars) < target:
                remaining = [v for v in vars_ if v not in free_vars]
                need = min(len(remaining), target - len(free_vars))
                if need > 0:
                    free_vars |= set(rng.sample(remaining, need))

        if len(free_vars) >= len(vars_):
            keep = rng.choice(vars_)
            free_vars.remove(keep)

        partial = {v: assignment[v] for v in vars_ if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, window_bias: float = 0.7):
    return PeriodChunkDestruction(problem, ratio, window_bias)
