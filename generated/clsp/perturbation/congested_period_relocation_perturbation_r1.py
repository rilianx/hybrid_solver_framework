from random import Random
from typing import List, Tuple

COMPONENT = {
    "name": "congested_period_relocation_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 6.0]},
        "window": {"type": "int", "range": [1, 4]},
    },
}


class CongestedPeriodRelocationPerturbation:
    """Kicks by relocating setups away from the most congested periods."""

    def __init__(self, problem, window: int = 2):
        self.problem = problem
        self.inst = problem.inst
        self.window = max(1, int(window))

    def _copy(self, sol):
        return tuple(tuple(row) for row in sol)

    def _set(self, sol, i: int, t: int, value: bool):
        rows = [list(row) for row in sol]
        rows[i][t] = value
        return tuple(tuple(row) for row in rows)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        k = max(1, int(round(strength)))

        # Measure congestion by setups + setup times already present.
        period_loads = []
        for t in range(n_periods):
            load = sum(inst.setup_time[i] for i in range(n_items) if sol[i][t])
            period_loads.append((load / max(inst.capacity[t], 1e-9), t))
        period_loads.sort(reverse=True)

        new_sol = self._copy(sol)
        changed = False

        for _, t in period_loads[: min(n_periods, k)]:
            candidates = [i for i in range(n_items) if new_sol[i][t]]
            rng.shuffle(candidates)
            if not candidates:
                continue
            i = candidates[0]

            # Try moving the setup to a nearby period with some preference for slack.
            options: List[int] = []
            for dt in range(1, self.window + 1):
                if t - dt >= 0:
                    options.append(t - dt)
                if t + dt < n_periods:
                    options.append(t + dt)
            rng.shuffle(options)

            moved = False
            for u in options:
                if u == t:
                    continue
                cand = self._set(new_sol, i, t, False)
                cand = self._set(cand, i, u, True)
                if cand != sol:
                    new_sol = cand
                    changed = True
                    moved = True
                    break

            if not moved:
                # Fallback: flip another setup bit in the same period to guarantee a change.
                j = rng.randrange(n_items)
                if j != i:
                    cand = self._set(new_sol, j, t, not new_sol[j][t])
                    if cand != sol:
                        new_sol = cand
                        changed = True
                        break

        if not changed:
            # Absolute fallback: toggle the first available bit.
            for i in range(n_items):
                for t in range(n_periods):
                    cand = self._set(sol, i, t, not sol[i][t])
                    if cand != sol:
                        return cand
        return new_sol


def build_component(problem, **params):
    window = params.get("window", 2)
    return CongestedPeriodRelocationPerturbation(problem, window=window)
