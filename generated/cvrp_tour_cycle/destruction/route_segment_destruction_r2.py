from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "route_segment_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.from_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class RouteSegmentDestruction:
    """Libera un segmento contiguo del gran tour, traducido a variables de arcos."""

    def __init__(self, problem, **params):
        self.problem = problem

    def _tour_from_assignment(self, assignment: dict[str, float]) -> list[int]:
        succ: dict[int, int] = {}
        pred: dict[int, int] = {}

        for name, val in assignment.items():
            if val <= 0.5 or not name.startswith("x_"):
                continue
            parts = name.split("_")
            if len(parts) != 3:
                continue
            try:
                i = int(parts[1])
                j = int(parts[2])
            except ValueError:
                continue
            succ[i] = j
            pred[j] = i

        start = None
        for node in succ:
            if node != 0 and node not in pred:
                start = node
                break

        if start is None:
            return []

        tour: list[int] = []
        cur = start
        seen: set[int] = set()
        while cur != 0 and cur not in seen:
            tour.append(cur)
            seen.add(cur)
            cur = succ.get(cur, 0)
        return tour

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = dict(self.problem.to_assignment(sol))
        tour = self._tour_from_assignment(assignment)

        if not tour:
            keys = list(assignment.keys())
            if not keys:
                return assignment, set()
            k = max(1, int(round(ratio * len(keys))))
            k = min(k, len(keys))
            chosen = set(rng.sample(keys, k))
            partial = {v: val for v, val in assignment.items() if v not in chosen}
            return partial, chosen

        n = len(tour)
        seg_len = max(1, int(round(ratio * n)))
        seg_len = min(seg_len, n)

        start = rng.randrange(0, n - seg_len + 1)
        segment = tour[start : start + seg_len]

        freed: set[str] = set()
        segment_set = set(segment)

        prev = 0 if start == 0 else tour[start - 1]
        first = segment[0]
        last = segment[-1]
        nxt = 0 if start + seg_len >= n else tour[start + seg_len]

        if f"x_{prev}_{first}" in assignment:
            freed.add(f"x_{prev}_{first}")
        if f"x_{last}_{nxt}" in assignment:
            freed.add(f"x_{last}_{nxt}")

        for idx, node in enumerate(segment):
            if idx > 0:
                p = segment[idx - 1]
                var = f"x_{p}_{node}"
                if var in assignment:
                    freed.add(var)
            if idx + 1 < len(segment):
                q = segment[idx + 1]
                var = f"x_{node}_{q}"
                if var in assignment:
                    freed.add(var)

        for node in segment_set:
            for var in (f"x_{0}_{node}", f"x_{node}_{0}"):
                if var in assignment:
                    freed.add(var)

        if not freed:
            keys = list(assignment.keys())
            k = max(1, int(round(ratio * len(keys))))
            k = min(k, len(keys))
            freed = set(rng.sample(keys, k))

        partial = {v: val for v, val in assignment.items() if v not in freed}
        return partial, freed


def build_component(problem, **params):
    ratio = params.get("ratio", 0.2)
    return RouteSegmentDestruction(problem, ratio=ratio)
