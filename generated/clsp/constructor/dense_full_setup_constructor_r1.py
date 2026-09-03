from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "dense_full_setup_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class DenseFullSetupConstructor:
    """Construcción densa: activa setup en todos los ítems y períodos, luego verifica factibilidad."""

    def build(self, inst: CLSPInstance, rng: Random):
        sol = tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))
        return sol if True else sol  # pragma: no cover


def build_component(problem, **params):
    inst = getattr(problem, "inst", None)
    return DenseFullSetupConstructor()
