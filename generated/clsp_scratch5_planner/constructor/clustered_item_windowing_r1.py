from __future__ import annotations

from random import Random
from math import ceil
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
    """Agrupa ítems por ventanas temporales y asigna setups coordinando capacidad entre ítems compatibles.

    La idea es:
    1) clusterizar ítems por el momento donde concentran su demanda;
    2) dentro de cada ventana, formar pocos lotes para ítems con holding barato y más cortos para los caros;
    3) colocar esos lotes en períodos con holgura, respetando capacidad y cubriendo toda la demanda.
    """

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
        out = []
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
                peak = max(range(inst.n_periods), key=lambda t: dem[t])
                centroid = sum(t * dem[t] for t in range(inst.n_periods)) / total
            feats.append((i, total, inst.holding_cost[i], inst.setup_cost[i], inst.setup_time[i], peak, centroid))
        return feats

    def _build_segments(self, inst: CLSPInstance, item: int, rng: Random) -> List[Tuple[int, int, float]]:
        """Return list of segments (start, end_exclusive, load) for one item."""
        dem = inst.demand[item]
        periods = [t for t, q in enumerate(dem) if q > 0]
        if not periods:
            return []

        total = sum(dem)
        h = inst.holding_cost[item]
        # Cheap holding -> longer lots -> fewer segments.
        desired = 1 + int((h / max(1.0, max(inst.holding_cost))) * (1.5 + self.split_bias))
        desired = max(1, min(desired, len(periods), 4))

        # Slight randomness for tie breaking, deterministic via rng.
        if len(periods) > 1 and rng.random() < 0.25:
            desired = min(len(periods), desired + 1)

        # Quantile-like cuts on positive-demand periods.
        cuts = [periods[0]]
        if desired > 1:
            for q in range(1, desired):
                idx = int(round(q * len(periods) / desired))
                idx = min(max(1, idx), len(periods) - 1)
                cuts.append(periods[idx])
        cuts = sorted(set(cuts))
        if cuts[-1] != periods[-1]:
            cuts.append(periods[-1] + 1)

        segments = []
        for a, b in zip(cuts[:-1], cuts[1:]):
            load = sum(dem[t] for t in range(a, b))
            if load > 0:
                segments.append((a, b, load))
        if not segments:
            segments = [(periods[0], periods[-1] + 1, total)]
        return segments

    def _assign_segments(self, inst: CLSPInstance, items: List[int], rng: Random):
        nT = inst.n_periods
        remaining = [float(c) for c in inst.capacity]
        sol = [[False] * nT for _ in range(inst.n_items)]

        # Precompute all segments and process larger / later-risky ones first.
        segs = []
        for i in items:
            for a, b, load in self._build_segments(inst, i, rng):
                segs.append((load, b - a, a, b, i))
        segs.sort(key=lambda x: (-(x[0]), -(x[1]), x[4]))

        for load, _span, a, b, i in segs:
            st = inst.setup_time[i]
            # Candidate setup periods must be within the segment start and before end.
            candidates = list(range(a, b))
            if not candidates:
                candidates = [min(a, nT - 1)]
            # Prefer periods with more remaining capacity and closer to the segment start.
            candidates.sort(key=lambda t: (-remaining[t], abs(t - a), t))
            placed = False
            for t in candidates:
                need = load + st
                if remaining[t] + 1e-9 >= need:
                    sol[i][t] = True
                    remaining[t] -= need
                    placed = True
                    break
            if not placed:
                # Try to split the segment by adding an intermediate setup around the midpoint.
                if b - a > 1:
                    mid = (a + b) // 2
                    parts = [(a, mid), (mid, b)]
                    part_loads = [sum(inst.demand[i][tt] for tt in range(x, y)) for x, y in parts]
                    # Greedily place the larger subsegment first.
                    order = [0, 1] if part_loads[0] >= part_loads[1] else [1, 0]
                    for idx in order:
                        x, y = parts[idx]
                        lq = part_loads[idx]
                        cand2 = list(range(x, y)) or [min(x, nT - 1)]
                        cand2.sort(key=lambda t: (-remaining[t], abs(t - x), t))
                        for t in cand2:
                            need = lq + st
                            if remaining[t] + 1e-9 >= need:
                                sol[i][t] = True
                                remaining[t] -= need
                                placed = True
                                break
                        if placed:
                            break
                if not placed:
                    # Last resort: put it in the least loaded feasible period, even if tight.
                    t = max(range(a, b), key=lambda tt: remaining[tt]) if a < b else min(a, nT - 1)
                    sol[i][t] = True
                    remaining[t] -= load + st

        return tuple(tuple(row) for row in sol)

    def build(self, inst: CLSPInstance, rng: Random):
        feats = self._item_features(inst)
        nT = inst.n_periods

        # Cluster items by temporal demand signature.
        feats.sort(key=lambda z: (z[5], z[6], z[2], z[0]))  # peak, centroid, holding, id
        window = max(1, int(round(self.window_frac * nT)))
        # number of clusters/windows
        k = max(1, ceil(len(feats) / max(1, window)))
        clusters = self._chunks([i for i, *_ in feats], k)

        # Build within-cluster assignment; if infeasible, relax clustering by more windows.
        best = None
        for extra in range(3):
            cand_items = []
            for cl in clusters:
                # In each cluster, items with low holding are packed earlier/more aggressively.
                cl_sorted = sorted(
                    cl,
                    key=lambda i: (
                        inst.holding_cost[i] * self.holding_bias,
                        -sum(inst.demand[i]),
                        max(range(nT), key=lambda t: inst.demand[i][t]),
                        i,
                    ),
                )
                cand_items.extend(cl_sorted)

            sol = self._assign_segments(inst, cand_items, rng)
            if self.problem.is_feasible(sol):
                return sol
            best = sol

            # Repair strategy: increase segmentation for expensive-holding items and redistribute.
            # This makes more use of early capacity for cheap items and shorter lots for costly ones.
            self.split_bias += 0.35
            clusters = self._chunks(cand_items, min(len(cand_items), k + extra + 1))

        # Final deterministic repair: if still infeasible, aggressively add early coverage.
        # We keep the pattern structured but make every positive-demand item start earlier.
        if not self.problem.is_feasible(best):
            sol = [list(r) for r in best]
            for i in range(inst.n_items):
                dem = inst.demand[i]
                if sum(dem) <= 0:
                    continue
                first = next((t for t, q in enumerate(dem) if q > 0), 0)
                # Ensure at least one setup before first demand and one near the peak if needed.
                peak = max(range(inst.n_periods), key=lambda t: dem[t])
                sol[i][min(first, peak)] = True
                if inst.holding_cost[i] > min(inst.holding_cost) and peak + 1 < inst.n_periods:
                    sol[i][peak] = True
            sol = tuple(tuple(r) for r in sol)
            if self.problem.is_feasible(sol):
                return sol

        return best


def build_component(problem, window_frac: float = 0.3, holding_bias: float = 1.5, split_bias: float = 1.0):
    return ClusteredItemWindowingConstructor(
        problem,
        window_frac=window_frac,
        holding_bias=holding_bias,
        split_bias=split_bias,
    )
