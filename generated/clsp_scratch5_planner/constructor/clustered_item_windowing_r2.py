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
    """Constructor por ventanas de ítems con lotificación y coordinación de capacidad."""

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

        # Cheap holding -> larger batches; expensive holding -> finer segmentation.
        desired = 1 + int((h / max(1.0, max_h)) * (1.0 + self.split_bias))
        desired = max(1, min(desired, len(periods), 6))

        # Split positive-demand periods into contiguous windows.
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

        # Build item segments and place larger/later segments first.
        segs = []
        for i in items:
            for a, b, load in self._build_segments(inst, i):
                segs.append((load, b - a, a, b, i))
        segs.sort(key=lambda x: (-x[0], -x[1], x[4], x[2]))

        for load, _span, a, b, i in segs:
            st = inst.setup_time[i]
            # Prefer the latest feasible period in the window to limit inventory.
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
                # Split the window once around the midpoint, still using elemental placements.
                if b - a > 1:
                    mid = (a + b) // 2
                    parts = [(a, mid), (mid, b)]
                    part_loads = [sum(inst.demand[i][tt] for tt in range(x, y_)) for x, y_ in parts]
                    order = [0, 1] if part_loads[0] >= part_loads[1] else [1, 0]
                    for idx in order:
                        x, y_ = parts[idx]
                        lq = part_loads[idx]
                        cand2 = list(range(min(y_ - 1, nT - 1), max(-1, x - 1), -1))
                        for t in cand2:
                            need = lq + st
                            if remaining[t] + 1e-9 >= need:
                                y[i][t] = True
                                remaining[t] -= need
                                placed = True
                                break
                        if placed:
                            break
            if not placed:
                # Deterministic last resort: choose the window period with the largest remaining capacity.
                cand = list(range(max(0, a), min(b, nT)))
                if not cand:
                    cand = [max(0, min(nT - 1, a))]
                t = max(cand, key=lambda tt: (remaining[tt], -tt))
                y[i][t] = True
                remaining[t] -= (load + st)

        return tuple(tuple(row) for row in y)

    def _repair_by_forcing_early_setups(self, inst: CLSPInstance, sol: Tuple[Tuple[bool, ...], ...]) -> Tuple[Tuple[bool, ...], ...]:
        # Structural repair focused on the validator's failure mode: missing setups before early demand.
        nT = inst.n_periods
        y = [list(row) for row in sol]
        for i in range(inst.n_items):
            dem = inst.demand[i]
            if sum(dem) <= 0:
                continue
            first = next((t for t, q in enumerate(dem) if q > 0), 0)
            peak = max(range(nT), key=lambda t: (dem[t], -t)) if nT > 0 else 0
            # Ensure there is at least one setup at or before the first positive-demand period.
            y[i][min(first, peak)] = True
        return tuple(tuple(row) for row in y)

    def build(self, inst: CLSPInstance, rng: Random):
        feats = self._item_features(inst)
        nT = inst.n_periods

        # Cluster items by temporal demand signature.
        feats.sort(key=lambda z: (z[5], z[6], z[2], z[0]))  # peak, centroid, holding, id
        window = max(1, int(round(self.window_frac * nT)))
        k = max(1, ceil(len(feats) / max(1, window)))
        clusters = self._chunks([i for i, *_ in feats], k)

        ordered_items: List[int] = []
        for cl in clusters:
            # Low holding items are packed more aggressively; expensive ones are spread.
            cl_sorted = sorted(
                cl,
                key=lambda i: (
                    inst.holding_cost[i] * self.holding_bias,
                    -sum(inst.demand[i]),
                    max(range(nT), key=lambda t: (inst.demand[i][t], -t)),
                    i,
                ),
            )
            ordered_items.extend(cl_sorted)

        sol = self._assign_segments(inst, ordered_items)
        if self.problem.is_feasible(sol):
            return sol

        repaired = self._repair_by_forcing_early_setups(inst, sol)
        if self.problem.is_feasible(repaired):
            return repaired

        # Final fallback: greedy prefix-feasibility repair by adding setups at earliest demand periods.
        y = [list(row) for row in repaired]
        for i in range(inst.n_items):
            dem = inst.demand[i]
            if sum(dem) <= 0:
                continue
            first = next((t for t, q in enumerate(dem) if q > 0), 0)
            y[i][first] = True
        repaired = tuple(tuple(row) for row in y)
        return repaired


def build_component(problem, window_frac: float = 0.3, holding_bias: float = 1.5, split_bias: float = 1.0):
    return ClusteredItemWindowingConstructor(
        problem,
        window_frac=window_frac,
        holding_bias=holding_bias,
        split_bias=split_bias,
    )
