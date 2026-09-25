from random import Random

from examples.lotsizing.problem_model import Solution  # type: ignore

COMPONENT = {
    "name": "congestion_based_setup_swap",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class CongestionBasedSetupSwap:
    def __init__(self, problem):
        self.problem = problem

    @staticmethod
    def _copy(sol):
        return [list(row) for row in sol]

    def perturb(self, sol: Solution, strength: float, rng: Random) -> Solution:
        inst = self.problem.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        k = max(1, int(round(strength)))

        y = self._copy(sol)

        # Congestion score per period: setups already active + "pressure" from demand/capacity.
        period_scores = []
        for t in range(n_periods):
            active_setups = sum(1 for i in range(n_items) if y[i][t])
            demand_pressure = sum(inst.demand[i][t] for i in range(n_items)) / max(inst.capacity[t], 1e-9)
            period_scores.append((active_setups + demand_pressure, t))
        period_scores.sort(reverse=True)
        hot_periods = [t for _, t in period_scores[: max(1, min(3, n_periods))]]

        for _ in range(k):
            if n_items == 0 or n_periods == 0:
                break

            t_hot = hot_periods[rng.randrange(len(hot_periods))]
            items_on = [i for i in range(n_items) if y[i][t_hot]]
            items_off = [i for i in range(n_items) if not y[i][t_hot]]

            # Prefer a swap: turn off one setup in a congested period and turn on another item there.
            if items_on and items_off:
                i_off = items_on[rng.randrange(len(items_on))]
                i_on = items_off[rng.randrange(len(items_off))]
                y[i_off][t_hot] = False
                y[i_on][t_hot] = True
                continue

            # Fallback: move a setup from congested period to a neighboring one.
            if items_on:
                i = items_on[rng.randrange(len(items_on))]
                candidates = []
                if t_hot > 0:
                    candidates.append(t_hot - 1)
                if t_hot + 1 < n_periods:
                    candidates.append(t_hot + 1)
                if candidates:
                    nt = candidates[rng.randrange(len(candidates))]
                    y[i][t_hot] = False
                    y[i][nt] = True

        return tuple(tuple(row) for row in y)


def build_component(problem, strength: float = 2.0):
    return CongestionBasedSetupSwap(problem)
