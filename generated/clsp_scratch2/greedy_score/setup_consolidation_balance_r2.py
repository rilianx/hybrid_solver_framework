from __future__ import annotations

from typing import Any

COMPONENT = {
    "name": "setup_consolidation_balance",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "reuse_weight": {"type": "float", "range": [0.0, 5.0]},
        "balance_weight": {"type": "float", "range": [0.0, 5.0]},
        "earliness_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class SetupConsolidationBalance:
    """Puntúa acciones constructivas favoreciendo reutilización de setups y
    evitando concentrar demasiada carga en un período ya tensionado.

    Menor es mejor.
    """

    def __init__(
        self,
        problem,
        reuse_weight: float = 1.0,
        balance_weight: float = 1.0,
        earliness_weight: float = 1.0,
    ):
        self.inst = problem.inst
        self.reuse_weight = reuse_weight
        self.balance_weight = balance_weight
        self.earliness_weight = earliness_weight

    def _get(self, obj: Any, name: str, default: Any) -> Any:
        return getattr(obj, name, default)

    def score(self, partial, action) -> float:
        inst = self.inst

        item = self._get(action, "item", 0)
        source = self._get(action, "source", self._get(action, "period", 0))
        target = self._get(action, "period", source)
        qty = float(self._get(action, "qty", 0.0))

        setup_matrix = self._get(partial, "setup", None)
        already_setup = False
        if setup_matrix is not None:
            try:
                already_setup = bool(setup_matrix[item][source])
            except Exception:
                already_setup = False

        # Reutilizar un setup ya activo en el período origen es mejor.
        reuse_term = 0.0 if already_setup else 1.0

        # Balance: penaliza cargar más un período ya usado.
        used = self._get(partial, "used", None)
        if used is not None:
            try:
                used_source = float(used[source])
            except Exception:
                used_source = 0.0
        else:
            used_source = 0.0

        capacity = 1.0
        try:
            capacity = max(float(inst.capacity[source]), 1e-12)
        except Exception:
            capacity = 1.0

        setup_time = 0.0
        try:
            setup_time = 0.0 if already_setup else float(inst.setup_time[item])
        except Exception:
            setup_time = 0.0

        balance_term = (used_source + setup_time + max(qty, 0.0)) / capacity

        # Favorece fuentes más tempranas cuando todo lo demás empata.
        n_periods = int(getattr(inst, "n_periods", 1))
        earliness_term = 0.0
        if n_periods > 1:
            earliness_term = max(target - source, 0) / float(n_periods - 1)

        # Ligera penalización por fragmentación global si está disponible.
        fragmentation = 0.0
        if used is not None:
            try:
                active = 0
                for tt in range(n_periods):
                    if float(used[tt]) > 1e-12:
                        active += 1
                fragmentation = active / float(max(n_periods, 1))
            except Exception:
                fragmentation = 0.0

        return (
            self.reuse_weight * reuse_term
            + self.balance_weight * balance_term
            + self.earliness_weight * earliness_term
            + 0.15 * fragmentation
        )


def build_component(problem, reuse_weight: float = 1.0, balance_weight: float = 1.0, earliness_weight: float = 1.0):
    return SetupConsolidationBalance(problem, reuse_weight, balance_weight, earliness_weight)
