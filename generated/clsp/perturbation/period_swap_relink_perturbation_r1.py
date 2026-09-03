from random import Random

COMPONENT = {
    "name": "period_swap_relink_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 6.0]},
        "radius": {"type": "int", "range": [1, 3]},
    },
}


class PeriodSwapRelinkPerturbation:
    """Kicks by swapping setup activity between two items in a selected period and relinking nearby."""

    def __init__(self, problem, radius: int = 1):
        self.problem = problem
        self.inst = problem.inst
        self.radius = max(1, int(radius))

    def _set(self, sol, i: int, t: int, value: bool):
        rows = [list(row) for row in sol]
        rows[i][t] = value
        return tuple(tuple(row) for row in rows)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        k = max(1, int(round(strength)))

        # Focus on a period with many setups to create a structured shake.
        period_scores = []
        for t in range(n_periods):
            count = sum(1 for i in range(n_items) if sol[i][t])
            period_scores.append((count, t))
        period_scores.sort(reverse=True)

        new_sol = sol
        for _, t in period_scores[: min(k, n_periods)]:
            ones = [i for i in range(n_items) if new_sol[i][t]]
            zeros = [i for i in range(n_items) if not new_sol[i][t]]
            if not ones or not zeros:
                continue

            i = rng.choice(ones)
            j = rng.choice(zeros)

            # Swap a setup presence between two items at the chosen period.
            cand = self._set(new_sol, i, t, False)
            cand = self._set(cand, j, t, True)

            # Relink locally around the same items to keep the shake nontrivial.
            for _ in range(max(0, self.radius - 1)):
                if rng.random() < 0.5:
                    u = max(0, min(n_periods - 1, t + rng.choice([-1, 1]) * rng.randint(1, self.radius)))
                    cand = self._set(cand, i, u, not cand[i][u])
                else:
                    u = max(0, min(n_periods - 1, t + rng.choice([-1, 1]) * rng.randint(1, self.radius)))
                    cand = self._set(cand, j, u, not cand[j][u])

            if cand != sol:
                new_sol = cand

        if new_sol == sol:
            for i in range(n_items):
                for t in range(n_periods):
                    cand = self._set(sol, i, t, not sol[i][t])
                    if cand != sol:
                        return cand
        return new_sol


def build_component(problem, **params):
    radius = params.get("radius", 1)
    return PeriodSwapRelinkPerturbation(problem, radius=radius)
