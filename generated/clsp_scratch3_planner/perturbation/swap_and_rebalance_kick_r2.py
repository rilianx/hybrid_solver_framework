from random import Random

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

    def _to_tuple(self, s):
        return tuple(tuple(bool(v) for v in row) for row in s)

    def _period_pressure(self, sol):
        inst = self.inst
        scores = []
        for t in range(inst.n_periods):
            setups = [i for i in range(inst.n_items) if sol[i][t]]
            setup_time = sum(inst.setup_time[i] for i in setups)
            setup_cost = sum(inst.setup_cost[i] for i in setups)
            score = setup_time + 0.001 * setup_cost + 0.1 * len(setups)
            scores.append((score, t))
        scores.sort(reverse=True)
        return scores

    def _neighbors(self, t):
        neigh = []
        if t > 0:
            neigh.append(t - 1)
        if t + 1 < self.inst.n_periods:
            neigh.append(t + 1)
        return neigh

    def _apply_swap(self, s, i, t, j, u):
        s[i][t] = False
        s[i][u] = True
        s[j][u] = False
        s[j][t] = True

    def _apply_move(self, s, i, t, u):
        s[i][t] = False
        s[i][u] = True

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        m = max(1, int(round(strength)))

        s = self._copy_solution(sol)
        pressure = self._period_pressure(sol)

        # More strength => more elementary rebalancing moves.
        # Each move targets a congested period and a nearby period.
        for step in range(m):
            if not pressure:
                break
            _, t = pressure[step % len(pressure)]
            neigh = self._neighbors(t)
            if not neigh:
                continue
            u = rng.choice(neigh)

            items_t = [i for i in range(n_items) if s[i][t]]
            items_u = [j for j in range(n_items) if s[j][u]]
            rng.shuffle(items_t)
            rng.shuffle(items_u)

            did = False

            # Preferred elementary move: swap one setup in the congested period with one in a neighbor.
            for i in items_t:
                for j in items_u:
                    if i == j:
                        continue
                    if s[i][u] or s[j][t]:
                        continue
                    self._apply_swap(s, i, t, j, u)
                    did = True
                    break
                if did:
                    break

            # Fallback: move one setup from the congested period to the neighbor.
            if not did:
                for i in items_t:
                    if not s[i][u]:
                        self._apply_move(s, i, t, u)
                        did = True
                        break

            # Final fallback: activate a nearby setup if the congested period is empty.
            if not did:
                free_items = [i for i in range(n_items) if not s[i][u]]
                if free_items:
                    i = rng.choice(free_items)
                    s[i][u] = True

        cand = self._to_tuple(s)
        if cand != sol:
            return cand

        # Guaranteed change with minimum disturbance.
        t = max(range(n_periods), key=lambda tt: sum(1 for i in range(n_items) if sol[i][tt]))
        neigh = self._neighbors(t)
        if neigh:
            u = rng.choice(neigh)
            items_t = [i for i in range(n_items) if sol[i][t]]
            if items_t:
                i = rng.choice(items_t)
                s = self._copy_solution(sol)
                s[i][t] = False
                s[i][u] = True
                cand = self._to_tuple(s)
                if cand != sol:
                    return cand

        # Last resort: flip one bit.
        s = self._copy_solution(sol)
        for _ in range(50):
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s[i][t] = not s[i][t]
            cand = self._to_tuple(s)
            if cand != sol:
                return cand

        return self._to_tuple(s)


def build_component(problem, strength: float = 3.0):
    return SwapAndRebalanceKick(problem)
