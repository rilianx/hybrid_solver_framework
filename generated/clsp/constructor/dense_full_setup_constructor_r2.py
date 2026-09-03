from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "dense_full_setup_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class DenseFullSetupConstructor:
    """Construcción densa pero recortada por soporte de demanda: activa setups solo en el tramo útil."""

    def build(self, inst: CLSPInstance, rng: Random):
        n_items = inst.n_items
        n_periods = inst.n_periods
        demand = inst.demand

        sol = []
        for i in range(n_items):
            row = [False] * n_periods

            first = None
            last = None
            for t in range(n_periods):
                if demand[i][t] > 0:
                    if first is None:
                        first = t
                    last = t

            if first is not None:
                for t in range(first, last + 1):
                    row[t] = True

            sol.append(tuple(row))

        return tuple(sol)


def build_component(problem, **params):
    _ = getattr(problem, "inst", None)
    return DenseFullSetupConstructor()
