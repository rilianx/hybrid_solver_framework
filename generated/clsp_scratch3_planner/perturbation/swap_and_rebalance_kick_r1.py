from random import Random
from typing import Sequence

COMPONENT = {
    "name": "swap_and_rebalance_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class SwapAndRebalanceKick:
    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def _copy_solution(self, sol):
        return [list(row) for row in sol]

    def _toggle(self, s, i: int, t: int, value: bool):
        s[i][t] = value

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        k = max(1, int(round(strength)))

        # Build a light congestion score per period: setups and estimated load.
        period_score = []
        for t in range(n_periods):
            setups = [i for i in range(n_items) if sol[i][t]]
            setup_time = sum(inst.setup_time[i] for i in setups)
            setup_cost = sum(inst.setup_cost[i] for i in setups)
            score = setup_time + 0.001 * setup_cost + len(setups)
            period_score.append((score, t))
        period_score.sort(reverse=True)

        best = None
        best_obj = None

        # Try several structured swaps around the most loaded periods.
        tries = min(max(4, 2 * k), n_items * max(1, n_periods - 1) * 3)
        for _, t in period_score[: min(n_periods, k + 1)]:
            neighbors = []
            if t > 0:
                neighbors.append(t - 1)
            if t + 1 < n_periods:
                neighbors.append(t + 1)
            if not neighbors:
                continue

            items_t = [i for i in range(n_items) if sol[i][t]]
            rng.shuffle(items_t)

            for u in neighbors:
                items_u = [j for j in range(n_items) if sol[j][u]]
                rng.shuffle(items_u)

                # Preferred move: exchange setups of two different items between neighboring periods.
                for i in items_t[:]:
                    for j in items_u[:]:
                        if i == j:
                            continue
                        if sol[i][u] or sol[j][t]:
                            continue

                        s = self._copy_solution(sol)
                        self._toggle(s, i, t, False)
                        self._toggle(s, i, u, True)
                        self._toggle(s, j, u, False)
                        self._toggle(s, j, t, True)

                        cand = tuple(tuple(row) for row in s)
                        if cand == sol:
                            continue
                        obj = self.problem.objective(cand)
                        if best is None or obj < best_obj:
                            best, best_obj = cand, obj

                # Fallback: swap one setup out of the congested period and activate another item in neighbor.
                free_in_u = [j for j in range(n_items) if not sol[j][u] and not sol[j][t]]
                rng.shuffle(free_in_u)
                for i in items_t[:]:
                    for j in free_in_u:
                        s = self._copy_solution(sol)
                        self._toggle(s, i, t, False)
                        self._toggle(s, i, u, True)
                        self._toggle(s, j, u, True)
                        cand = tuple(tuple(row) for row in s)
                        if cand == sol:
                            continue
                        obj = self.problem.objective(cand)
                        if best is None or obj < best_obj:
                            best, best_obj = cand, obj

            tries -= 1
            if tries <= 0:
                break

        if best is not None:
            return best

        # Absolute fallback: move a setup from the most congested period to a neighbor.
        for _, t in period_score:
            neighbors = []
            if t > 0:
                neighbors.append(t - 1)
            if t + 1 < n_periods:
                neighbors.append(t + 1)
            rng.shuffle(neighbors)
            items_t = [i for i in range(n_items) if sol[i][t]]
            rng.shuffle(items_t)
            for u in neighbors:
                for i in items_t:
                    if sol[i][u]:
                        continue
                    s = self._copy_solution(sol)
                    self._toggle(s, i, t, False)
                    self._toggle(s, i, u, True)
                    cand = tuple(tuple(row) for row in s)
                    if cand != sol:
                        return cand

        # Final fallback: flip one setup somewhere and one elsewhere to guarantee change.
        s = self._copy_solution(sol)
        for _ in range(50):
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            u = t - 1 if t > 0 and rng.random() < 0.5 else (t + 1 if t + 1 < n_periods else t)
            if u == t:
                continue
            s2 = self._copy_solution(sol)
            s2[i][t] = not s2[i][t]
            s2[i][u] = not s2[i][u]
            cand = tuple(tuple(row) for row in s2)
            if cand != sol:
                return cand

        return tuple(tuple(row) for row in s)


def build_component(problem, strength: float = 3.0):
    return SwapAndRebalanceKick(problem)
