from __future__ import annotations

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial

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
    """Puntúa por consolidación de setups y balance de carga.

    Menor es mejor. Favorece:
    - reutilizar un setup ya activo en el mismo período fuente;
    - concentrar cobertura en pocos períodos para reducir fragmentación;
    - evitar cargar demasiado un período ya tensionado.
    """

    def __init__(
        self,
        problem,
        reuse_weight: float = 1.0,
        balance_weight: float = 1.0,
        earliness_weight: float = 1.0,
    ):
        self.inst: CLSPInstance = problem.inst
        self.reuse_weight = reuse_weight
        self.balance_weight = balance_weight
        self.earliness_weight = earliness_weight

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i = action.item
        s = action.source
        t = action.period

        source_free = max(partial.free(s), 0.0)
        cap = max(inst.capacity[s], 1e-12)
        load_after = partial.used[s] + (0.0 if partial.setup[i][s] else inst.setup_time[i]) + min(action.qty, source_free)
        balance = load_after / cap

        reuse_term = 0.0 if partial.setup[i][s] else 1.0
        earliness_term = (t - s) / max(inst.n_periods - 1, 1)

        active_sources = 0
        for tt in range(inst.n_periods):
            if partial.used[tt] > 1e-12:
                active_sources += 1
        fragmentation = active_sources / max(inst.n_periods, 1)

        return (
            self.reuse_weight * reuse_term
            + self.balance_weight * balance
            + self.earliness_weight * earliness_term
            + 0.15 * fragmentation
        )


def build_component(problem, reuse_weight: float = 1.0, balance_weight: float = 1.0, earliness_weight: float = 1.0):
    return SetupConsolidationBalance(problem, reuse_weight, balance_weight, earliness_weight)
