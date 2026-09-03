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
    """Constructor voraz: cubre la demanda sin backlog usando setups lo más temprano posible,
    respetando una cota de capacidad para tiempos de setup por período.
    """

    def __init__(self, lookahead: int = 4, frontload_bias: float = 0.35):
        self.lookahead = lookahead
        self.frontload_bias = frontload_bias

    @staticmethod
    def _empty_solution(n_items: int, n_periods: int):
        return tuple(tuple(False for _ in range(n_periods)) for _ in range(n_items))

    @staticmethod
    def _positive_blocks(demand_row):
        blocks = []
        n = len(demand_row)
        t = 0
        while t < n:
            while t < n and demand_row[t] <= 0:
                t += 1
            if t >= n:
                break
            start = t
            while t < n and demand_row[t] > 0:
                t += 1
            blocks.append(start)
        return blocks

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        demand = inst.demand
        setup_time = inst.setup_time
        capacity = inst.capacity

        # Remaining capacity for setup times only; production will be handled by the LP.
        remaining_setup_cap = [float(capacity[t]) for t in range(n_periods)]
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # Process items with higher total demand first to reduce the chance of starving heavy items.
        item_order = list(range(n_items))
        item_order.sort(key=lambda i: (-sum(demand[i]), -sum(1 for v in demand[i] if v > 0), i))

        for i in item_order:
            blocks = self._positive_blocks(demand[i])
            if not blocks:
                continue

            # Assign each positive-demand block an earliest feasible setup, with a mild preference
            # for frontloading when there is abundant setup capacity.
            last_setup = -1
            for b_idx, b in enumerate(blocks):
                # Earliest desired time for this block.
                desired = b
                if b_idx == 0:
                    # For the first block, we may pull the setup slightly earlier if useful.
                    earliest = 0
                else:
                    # Later blocks can only be covered by setups at or before the block start.
                    earliest = last_setup + 1

                # Search backwards from desired to earliest for a feasible setup period.
                chosen = None
                for t in range(desired, earliest - 1, -1):
                    if remaining_setup_cap[t] >= setup_time[i]:
                        chosen = t
                        break

                if chosen is None:
                    # If no slot is available for this block, merge it into the previous one by
                    # skipping the setup. The previous setup remains the earliest cover.
                    # If there was no previous setup, use the earliest period with any remaining
                    # capacity, falling back to the first period.
                    if last_setup < 0:
                        fallback = None
                        for t in range(0, desired + 1):
                            if remaining_setup_cap[t] >= setup_time[i]:
                                fallback = t
                                break
                        if fallback is None:
                            # As a last resort, pick the least loaded feasible period if any;
                            # this preserves the "setup exists" invariant whenever possible.
                            best_t = None
                            best_load = None
                            for t in range(0, desired + 1):
                                if remaining_setup_cap[t] >= setup_time[i]:
                                    load = capacity[t] - remaining_setup_cap[t]
                                    if best_load is None or load < best_load:
                                        best_load = load
                                        best_t = t
                            chosen = best_t
                        else:
                            chosen = fallback

                    if chosen is None:
                        # No feasible new setup can be inserted; rely on the previous setup to
                        # cover this block through inventory.
                        continue

                sol[i][chosen] = True
                remaining_setup_cap[chosen] -= setup_time[i]
                last_setup = chosen

            # Safety net: ensure every item with demand has at least one setup.
            if not any(sol[i]):
                chosen = None
                # Prefer the earliest period with enough setup capacity.
                for t in range(n_periods):
                    if remaining_setup_cap[t] >= setup_time[i]:
                        chosen = t
                        break
                if chosen is None:
                    # If even that fails, choose the period with maximum residual capacity.
                    chosen = max(range(n_periods), key=lambda t: remaining_setup_cap[t])
                sol[i][chosen] = True
                remaining_setup_cap[chosen] -= setup_time[i]

        return tuple(tuple(row) for row in sol)


def build_component(problem, lookahead: int = 4, frontload_bias: float = 0.35):
    return EarliestCoverBacklogFree(lookahead=lookahead, frontload_bias=frontload_bias)
