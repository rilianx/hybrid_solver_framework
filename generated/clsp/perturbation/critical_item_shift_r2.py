from __future__ import annotations

from random import Random


COMPONENT = {
    "name": "critical_item_shift",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "aggressiveness": {"type": "float", "range": [0.2, 2.0]},
    },
}


class CriticalItemShift:
    def __init__(self, problem, aggressiveness: float = 1.0):
        self.problem = problem
        self.aggressiveness = aggressiveness

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.problem.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        # Rank items by "criticality": setup cost and how often they are active.
        scores = []
        for i in range(n_items):
            freq = sum(1 for t in range(n_periods) if sol[i][t])
            scores.append((inst.setup_cost[i] * (1.0 + 0.5 * freq), i))
        scores.sort(reverse=True)

        # Higher strength => more elementary shifts, hence larger expected distance.
        n_moves = max(1, int(round(self.aggressiveness * strength)))
        top_k = max(1, min(n_items, n_moves))
        chosen_items = [i for _, i in scores[:top_k]]

        s = [list(row) for row in sol]

        for _ in range(n_moves):
            chosen_item = rng.choice(chosen_items)

            active_periods = [t for t in range(n_periods) if s[chosen_item][t]]
            if active_periods:
                # Move one existing setup to a different period.
                t_from = rng.choice(active_periods)
                candidates = [t for t in range(n_periods) if t != t_from]
                if not candidates:
                    continue
                t_to = rng.choice(candidates)
                s[chosen_item][t_from] = False
                s[chosen_item][t_to] = True
            else:
                # If no setup exists for the selected item, add one setup elementarily.
                t = rng.randrange(n_periods)
                s[chosen_item][t] = True

        new_sol = tuple(tuple(row) for row in s)
        if new_sol == sol:
            # Guarantee a change when possible.
            chosen_item = rng.choice(chosen_items)
            t = rng.randrange(n_periods)
            s = [list(row) for row in sol]
            s[chosen_item][t] = not s[chosen_item][t]
            new_sol = tuple(tuple(row) for row in s)

        return new_sol


def build_component(problem, **params):
    return CriticalItemShift(
        problem,
        aggressiveness=float(params.get("aggressiveness", 1.0)),
    )
