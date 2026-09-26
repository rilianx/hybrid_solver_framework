from random import Random
from typing import Any

COMPONENT = {
    "name": "expensive_edge_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
        "mix_randomness": {"type": "float", "range": [0.0, 1.0]},
    },
}


class ExpensiveEdgeDestruction:
    """Libera arcos con mayor contribución directa al costo de la solución actual."""

    def __init__(self, problem, ratio: float = 0.25, mix_randomness: float = 0.2):
        self.problem = problem
        self.inst = problem.inst
        self.ratio = float(ratio)
        self.mix_randomness = float(mix_randomness)

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        all_vars = set(assignment)

        xvars = [v for v, val in assignment.items() if float(val) > 0.5]
        if not xvars:
            chosen = {rng.choice(sorted(all_vars))}
            partial = {v: val for v, val in assignment.items() if v not in chosen}
            return partial, chosen

        scored = []
        for v in xvars:
            try:
                _, i, j = v.split("_")
                i = int(i)
                j = int(j)
            except Exception:
                continue
            cost = float(self.inst.dist(i, j))
            # ruido controlado para diversificar
            noisy = cost * (1.0 + self.mix_randomness * rng.random())
            scored.append((noisy, v))

        scored.sort(reverse=True, key=lambda t: (t[0], t[1]))
        target = max(1, int(round(float(ratio) * len(all_vars))))

        free_vars = set(v for _, v in scored[:target])

        # Asegura al menos una variable liberada
        if not free_vars:
            free_vars = {rng.choice(sorted(all_vars))}

        # Mezcla unas pocas variables adicionales si el azar lo sugiere
        if self.mix_randomness > 0.0 and len(free_vars) < target:
            candidates = list(all_vars - free_vars)
            rng.shuffle(candidates)
            extra = int(round(self.mix_randomness * max(0, target - len(free_vars))))
            for v in candidates[:extra]:
                free_vars.add(v)

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, mix_randomness: float = 0.2):
    return ExpensiveEdgeDestruction(problem, ratio=ratio, mix_randomness=mix_randomness)
