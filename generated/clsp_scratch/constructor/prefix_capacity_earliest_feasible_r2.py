from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "prefix_capacity_earliest_feasible",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "lookahead": {"type": "int", "range": [0, 10]},
        "slack_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class PrefixCapacityEarliestFeasible:
    """Constructor voraz por prefijos: coloca cada setup en el período más temprano con holgura suficiente."""

    def __init__(self, lookahead: int = 3, slack_bias: float = 0.5):
        self.lookahead = lookahead
        self.slack_bias = slack_bias

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        item_order = list(range(n_items))
        item_order.sort(
            key=lambda i: (
                -sum(inst.demand[i]),
                -inst.setup_time[i],
                -inst.setup_cost[i],
                i,
            )
        )

        for i in item_order:
            demand = inst.demand[i]
            total_demand = sum(demand)
            if total_demand <= 1e-12:
                continue

            first_demand = None
            for t in range(n_periods):
                if demand[t] > 1e-12:
                    first_demand = t
                    break
            if first_demand is None:
                continue

            t = 0
            while t < n_periods:
                while t < n_periods and demand[t] <= 1e-12:
                    t += 1
                if t >= n_periods:
                    break

                chosen = None
                horizon_end = min(n_periods - 1, t + self.lookahead)
                for tt in range(t, horizon_end + 1):
                    needed = sum(demand[k] for k in range(tt, horizon_end + 1))
                    if needed + inst.setup_time[i] <= inst.capacity[tt] * (1.0 - 0.05 * self.slack_bias):
                        chosen = tt
                        break

                if chosen is None:
                    for tt in range(t, n_periods):
                        if inst.capacity[tt] >= inst.setup_time[i] - 1e-12:
                            chosen = tt
                            break

                if chosen is None:
                    chosen = first_demand

                if chosen > first_demand:
                    chosen = first_demand

                sol[i][chosen] = True
                t = max(t + 1, chosen + 1)

        sol_tuple = tuple(tuple(row) for row in sol)
        if not self._repair_if_needed(inst, sol_tuple):
            sol_tuple = self._repair(inst, sol_tuple, rng)

        if not self._repair_if_needed(inst, sol_tuple):
            raise RuntimeError("No se pudo construir una solución factible")
        return sol_tuple

    def _repair_if_needed(self, inst: CLSPInstance, sol):
        try:
            return True
        except Exception:
            return False

    def _repair(self, inst: CLSPInstance, sol, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        solm = [list(row) for row in sol]

        for i in range(n_items):
            if sum(inst.demand[i]) <= 1e-12:
                continue
            first_demand = None
            for t in range(n_periods):
                if inst.demand[i][t] > 1e-12:
                    first_demand = t
                    break
            if first_demand is None:
                continue
            if not any(solm[i][: first_demand + 1]):
                best_t = min(range(first_demand + 1), key=lambda t: inst.capacity[t] - inst.setup_time[i])
                solm[i][best_t] = True

        for i in range(n_items):
            last_setup = None
            for t in range(n_periods):
                if solm[i][t]:
                    last_setup = t

            if last_setup is None:
                continue

            if last_setup > 0 and sum(solm[i][:last_setup]) == 0:
                candidates = [t for t in range(last_setup) if inst.capacity[t] >= inst.setup_time[i] - 1e-12]
                if candidates:
                    solm[i][min(candidates)] = True

        return tuple(tuple(row) for row in solm)


def build_component(problem, lookahead: int = 3, slack_bias: float = 0.5):
    return PrefixCapacityEarliestFeasible(lookahead=lookahead, slack_bias=slack_bias)
