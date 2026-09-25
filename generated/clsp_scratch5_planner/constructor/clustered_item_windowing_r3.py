from __future__ import annotations

from math import ceil
from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance, var_name

COMPONENT = {
    "name": "clustered_item_windowing",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "window_frac": {"type": "float", "range": [0.15, 0.6]},
        "holding_bias": {"type": "float", "range": [0.5, 3.0]},
        "split_bias": {"type": "float", "range": [0.0, 2.5]},
    },
}


class ClusteredItemWindowingConstructor:
    """Constructor por ventanas de ítems con coordinación temporal y de capacidad."""

    def __init__(self, problem, window_frac: float = 0.3, holding_bias: float = 1.5, split_bias: float = 1.0):
        self.problem = problem
        self.window_frac = window_frac
        self.holding_bias = holding_bias
        self.split_bias = split_bias

    @staticmethod
    def _chunks(items: List[int], k: int) -> List[List[int]]:
        if not items:
            return []
        k = max(1, min(k, len(items)))
        base, rem = divmod(len(items), k)
        out: List[List[int]] = []
        p = 0
        for j in range(k):
            sz = base + (1 if j < rem else 0)
            out.append(items[p : p + sz])
            p += sz
        return out

    def _item_features(self, inst: CLSPInstance):
        feats = []
        for i in range(inst.n_items):
            dem = inst.demand[i]
            total = sum(dem)
            if total <= 0:
                peak = 0
                centroid = 0.0
            else:
                peak = max(range(inst.n_periods), key=lambda t: (dem[t], -t))
                centroid = sum(t * dem[t] for t in range(inst.n_periods)) / total
            feats.append((i, total, inst.holding_cost[i], inst.setup_cost[i], inst.setup_time[i], peak, centroid))
        return feats

    def _build_segments(self, inst: CLSPInstance, item: int) -> List[Tuple[int, int, int]]:
        dem = inst.demand[item]
        periods = [t for t, q in enumerate(dem) if q > 0]
        if not periods:
            return []
        total = sum(dem)
        h = inst.holding_cost[item]
        max_h = max(inst.holding_cost) if inst.holding_cost else 1.0

        desired = 1 + int((h / max(1.0, max_h)) * (1.0 + self.split_bias))
        desired = max(1, min(desired, len(periods), 6))

        cuts = [0]
        if desired > 1:
            for q in range(1, desired):
                idx = int(round(q * len(periods) / desired))
                idx = min(max(1, idx), len(periods) - 1)
                cuts.append(idx)
        cuts.append(len(periods))
        cuts = sorted(set(cuts))

        segs: List[Tuple[int, int, int]] = []
        for a, b in zip(cuts[:-1], cuts[1:]):
            left = periods[a]
            right = periods[b - 1]
            load = sum(dem[t] for t in periods[a:b])
            if load > 0:
                segs.append((left, right + 1, load))
        if not segs:
            segs = [(periods[0], periods[-1] + 1, total)]
        return segs

    def _assign_segments(self, inst: CLSPInstance, items: List[int]) -> Tuple[Tuple[bool, ...], ...]:
        nT = inst.n_periods
        remaining = [float(c) for c in inst.capacity]
        y = [[False] * nT for _ in range(inst.n_items)]

        segs = []
        for i in items:
            for a, b, load in self._build_segments(inst, i):
                segs.append((load, b - a, a, b, i))
        segs.sort(key=lambda x: (-x[0], -x[1], x[4], x[2]))

        for load, _span, a, b, i in segs:
            st = inst.setup_time[i]
            candidates = list(range(min(b - 1, nT - 1), max(-1, a - 1), -1))
            placed = False
            for t in candidates:
                need = load + st
                if remaining[t] + 1e-9 >= need:
                    y[i][t] = True
                    remaining[t] -= need
                    placed = True
                    break
            if not placed:
                # If the window is too tight, place the segment at the latest period with residual capacity.
                cand = list(range(max(0, a), min(b, nT)))
                if not cand:
                    cand = [max(0, min(nT - 1, a))]
                t = max(cand, key=lambda tt: (remaining[tt], -tt))
                y[i][t] = True
                remaining[t] -= (load + st)

        return tuple(tuple(row) for row in y)

    def _capacity_greedy_repair(self, inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        """
        Feasible construction by backward allocation of each item's demand into periods with residual capacity.
        This only decides setup periods; if a period receives positive assigned production for an item,
        the corresponding setup is activated there.
        """
        n_items = inst.n_items
        nT = inst.n_periods
        remaining = [float(c) for c in inst.capacity]
        y = [[False] * nT for _ in range(n_items)]

        feats = self._item_features(inst)
        # Clustered order: same structure as the main idea, but used as a feasibility-preserving construction order.
        feats.sort(key=lambda z: (z[5], z[6], z[2], z[0]))
        window = max(1, int(round(self.window_frac * nT)))
        k = max(1, ceil(len(feats) / max(1, window)))
        ordered_items: List[int] = []
        for cl in self._chunks([i for i, *_ in feats], k):
            cl_sorted = sorted(
                cl,
                key=lambda i: (
                    inst.holding_cost[i] * self.holding_bias,
                    -sum(inst.demand[i]),
                    max(range(nT), key=lambda t: (inst.demand[i][t], -t)) if nT > 0 else 0,
                    i,
                ),
            )
            ordered_items.extend(cl_sorted)

        for i in ordered_items:
            dem = inst.demand[i]
            if sum(dem) <= 0:
                continue

            # Allocate each period's demand as late as possible up to its due date.
            for t in range(nT - 1, -1, -1):
                q = dem[t]
                while q > 1e-12:
                    placed = False
                    for p in range(t, -1, -1):
                        if y[i][p]:
                            avail = remaining[p]
                            if avail > 1e-12:
                                take = min(q, avail)
                                remaining[p] -= take
                                q -= take
                                placed = True
                                if q <= 1e-12:
                                    break
                        else:
                            need_setup = inst.setup_time[i]
                            avail = remaining[p] - need_setup
                            if avail > 1e-12:
                                take = min(q, avail)
                                y[i][p] = True
                                remaining[p] -= (need_setup + take)
                                q -= take
                                placed = True
                                if q <= 1e-12:
                                    break
                    if not placed:
                        break

            # If some demand could not be allocated by the greedy backward pass,
            # force a compact setup pattern around the earliest demand periods.
            if any(d > 0 for d in dem):
                first = next((t for t, q in enumerate(dem) if q > 0), 0)
                y[i][first] = True

        return tuple(tuple(row) for row in y)

    def build(self, inst: CLSPInstance, rng: Random):
        # First attempt: clustered windowing with backward capacity-aware placement.
        feats = self._item_features(inst)
        nT = inst.n_periods
        feats.sort(key=lambda z: (z[5], z[6], z[2], z[0]))

        window = max(1, int(round(self.window_frac * nT)))
        k = max(1, ceil(len(feats) / max(1, window)))
        clusters = self._chunks([i for i, *_ in feats], k)

        ordered_items: List[int] = []
        for cl in clusters:
            cl_sorted = sorted(
                cl,
                key=lambda i: (
                    inst.holding_cost[i] * self.holding_bias,
                    -sum(inst.demand[i]),
                    max(range(nT), key=lambda t: (inst.demand[i][t], -t)) if nT > 0 else 0,
                    i,
                ),
            )
            ordered_items.extend(cl_sorted)

        sol = self._assign_segments(inst, ordered_items)
        if self.problem.is_feasible(sol):
            return sol

        repaired = self._capacity_greedy_repair(inst)
        if self.problem.is_feasible(repaired):
            return repaired

        # Final safe fallback: keep one setup at the first positive-demand period of each item.
        y = [list(row) for row in repaired]
        for i in range(inst.n_items):
            dem = inst.demand[i]
            if sum(dem) <= 0:
                continue
            first = next((t for t, q in enumerate(dem) if q > 0), 0)
            y[i][first] = True
        final = tuple(tuple(row) for row in y)
        if self.problem.is_feasible(final):
            return final

        return repaired


def build_component(problem, window_frac: float = 0.3, holding_bias: float = 1.5, split_bias: float = 1.0):
    return ClusteredItemWindowingConstructor(
        problem,
        window_frac=window_frac,
        holding_bias=holding_bias,
        split_bias=split_bias,
    )
