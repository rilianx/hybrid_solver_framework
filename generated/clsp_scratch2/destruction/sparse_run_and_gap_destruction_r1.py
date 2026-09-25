from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "sparse_run_and_gap_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "gap_threshold": {"type": "float", "range": [0.0, 1.0]},
    },
}


class SparseRunAndGapDestruction:
    """
    Libera setups aislados y los huecos vecinos para favorecer fusiones de lotes y reprogramación local.
    Opera sobre patrones temporales por ítem, no por período ni por costo.
    """

    def __init__(self, problem, inst, gap_threshold: float = 0.5):
        self.problem = problem
        self.inst = inst
        self.gap_threshold = gap_threshold

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods

        candidates: list[tuple[int, int, float]] = []
        for i in range(n_items):
            on = [t for t in range(n_periods) if sol[i][t]]
            if not on:
                continue
            # Penaliza setups aislados: si hay huecos largos, el centro del bloque es candidato.
            for idx, t in enumerate(on):
                left_gap = t - on[idx - 1] - 1 if idx > 0 else t
                right_gap = on[idx + 1] - t - 1 if idx + 1 < len(on) else (n_periods - 1 - t)
                isolation = left_gap + right_gap
                if isolation >= self.gap_threshold * max(1, n_periods - 1):
                    candidates.append((i, t, float(isolation)))
            if len(on) == 1:
                candidates.append((i, on[0], float(n_periods)))

        if not candidates:
            # Fallback: liberar una ventana corta alrededor del primer período con setup.
            for i in range(n_items):
                for t in range(n_periods):
                    if sol[i][t]:
                        candidates.append((i, t, 1.0))
                        break
                if candidates:
                    break

        candidates.sort(key=lambda z: z[2], reverse=True)
        target = max(1, int(round(ratio * n_items * n_periods)))
        free_vars: set[str] = set()

        for i, t, _ in candidates:
            # Libera el punto y sus vecinos temporales para permitir fusionar o desplazar.
            for tt in (t - 1, t, t + 1):
                if 0 <= tt < n_periods:
                    free_vars.add(var_name(i, tt))
            if len(free_vars) >= target:
                break

        if len(free_vars) > target:
            chosen = list(free_vars)
            rng.shuffle(chosen)
            free_vars = set(chosen[: max(1, target)])

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.15, gap_threshold: float = 0.5):
    return SparseRunAndGapDestruction(problem, problem.inst, gap_threshold=gap_threshold)
