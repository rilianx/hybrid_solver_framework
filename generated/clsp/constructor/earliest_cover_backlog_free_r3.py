from random import Random

COMPONENT = {
    "name": "earliest_cover_backlog_free",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "lookahead": {"type": "int", "range": [1, 12]},
        "frontload_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class EarliestCoverBacklogFree:
    """Constructor greedy factible:
    asigna setups y producción por ítem en orden cronológico, priorizando cubrir
    la demanda lo antes posible y respetando la capacidad por período.
    """

    def __init__(self, lookahead: int = 4, frontload_bias: float = 0.35):
        self.lookahead = lookahead
        self.frontload_bias = frontload_bias

    @staticmethod
    def _positive_periods(demand_row):
        return [t for t, d in enumerate(demand_row) if d > 0]

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        demand = inst.demand
        setup_time = inst.setup_time
        capacity = inst.capacity

        # Remaining per-period capacity available for "setup time + production".
        remaining = [float(capacity[t]) for t in range(n_periods)]
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # Heavier items first, but allow a tiny randomized tie-break to diversify.
        item_order = list(range(n_items))
        item_order.sort(
            key=lambda i: (
                -sum(demand[i]),
                -sum(1 for d in demand[i] if d > 0),
                i,
            )
        )

        # Greedy allocation:
        # For each item, traverse periods from early to late and place a setup whenever
        # there is remaining demand to cover and enough residual capacity to justify it.
        for i in item_order:
            total_demand = sum(demand[i])
            if total_demand <= 0:
                continue

            rem_demand = float(total_demand)
            first_positive = None
            positives = self._positive_periods(demand[i])
            if positives:
                first_positive = positives[0]

            # Primary pass: chronological, with a slight frontloading preference.
            for t in range(n_periods):
                if rem_demand <= 1e-9:
                    break

                # If we already have a setup for this item at t, just try to use remaining capacity.
                need_setup = not sol[i][t]

                # We can only place a setup if it leaves room for at least some production.
                # Keep a small slack to avoid tiny numerical issues.
                effective_cap = remaining[t] - float(setup_time[i])

                if need_setup and effective_cap <= 1e-9:
                    continue

                # Encourage earlier production when demand is already present, but not exclusively.
                urgency = 1.0
                if first_positive is not None and t > first_positive:
                    urgency = 0.85
                if t < first_positive if first_positive is not None else False:
                    urgency = 1.15

                if t == first_positive:
                    urgency *= (1.0 + 0.25 * self.frontload_bias)

                # Optional randomized skipping to diversify, but only when capacity is abundant.
                if need_setup and remaining[t] > 2.0 * float(setup_time[i]) and rng.random() > urgency:
                    continue

                # Open/setup item i in period t.
                if need_setup:
                    sol[i][t] = True
                    remaining[t] -= float(setup_time[i])

                # Produce as much as possible in this period.
                chunk = min(rem_demand, remaining[t])
                if chunk > 0:
                    remaining[t] -= chunk
                    rem_demand -= chunk

            # If demand remains, do a second pass allowing setup in any period with capacity.
            # This makes the constructor robust when early greedy choices are too conservative.
            if rem_demand > 1e-9:
                for t in range(n_periods):
                    if rem_demand <= 1e-9:
                        break
                    if sol[i][t]:
                        chunk = min(rem_demand, remaining[t])
                        if chunk > 0:
                            remaining[t] -= chunk
                            rem_demand -= chunk
                        continue

                    if remaining[t] <= float(setup_time[i]) + 1e-9:
                        continue

                    sol[i][t] = True
                    remaining[t] -= float(setup_time[i])
                    chunk = min(rem_demand, remaining[t])
                    if chunk > 0:
                        remaining[t] -= chunk
                        rem_demand -= chunk

            # Last-resort correction: if still unmet, place the item in the earliest
            # feasible period with any remaining capacity and consume it there.
            # This keeps the constructor feasible on instances where the greedy pass
            # left a gap due to competition for capacity.
            if rem_demand > 1e-9:
                for t in range(n_periods):
                    if remaining[t] > float(setup_time[i]) + 1e-9:
                        if not sol[i][t]:
                            sol[i][t] = True
                            remaining[t] -= float(setup_time[i])
                        chunk = min(rem_demand, remaining[t])
                        if chunk > 0:
                            remaining[t] -= chunk
                            rem_demand -= chunk
                        if rem_demand <= 1e-9:
                            break

        return tuple(tuple(row) for row in sol)


def build_component(problem, lookahead: int = 4, frontload_bias: float = 0.35):
    return EarliestCoverBacklogFree(lookahead=lookahead, frontload_bias=frontload_bias)
