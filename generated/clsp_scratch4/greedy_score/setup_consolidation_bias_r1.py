from __future__ import annotations

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "setup_consolidation_bias",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "consolidation_weight": {"type": "float", "range": [0.0, 10.0]},
        "inventory_weight": {"type": "float", "range": [0.0, 10.0]},
        "new_setup_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class SetupConsolidationBias:
    """Favorece consolidar demanda en menos setups del mismo ítem.

    Idea distinta:
    - si el ítem ya tiene setups activos, prefiere seguir usando ese patrón,
    - si la acción abre un nuevo setup, lo penaliza,
    - penaliza mucho mandar producción demasiado antes del período objetivo,
      porque dispersa inventario sin consolidar.

    Menor score = mejor.
    """

    def __init__(
        self,
        problem,
        consolidation_weight: float = 1.0,
        inventory_weight: float = 1.0,
        new_setup_weight: float = 1.0,
    ):
        self.inst: CLSPInstance = problem.inst
        self.consolidation_weight = float(consolidation_weight)
        self.inventory_weight = float(inventory_weight)
        self.new_setup_weight = float(new_setup_weight)

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i = action.item
        t = action.period
        s = action.source
        q = max(action.qty, 1e-12)

        # Ya hay setups del ítem: cuanto más, más conveniente seguir consolidando.
        existing_setups = sum(1 for tt in range(inst.n_periods) if partial.setup[i][tt])

        # Si abrimos un setup nuevo, lo penalizamos; si no, premiamos seguir usando la misma "familia".
        new_setup_penalty = self.new_setup_weight * (1.0 if action.new_setup else 0.0)

        # Consolidación: preferir ítems con setups ya existentes para evitar fragmentación.
        consolidation = self.consolidation_weight / (1.0 + existing_setups)

        # Inventario: producir muy temprano para un período lejano se penaliza.
        inventory = self.inventory_weight * max(0, t - s) * (inst.holding_cost[i] / q)

        # Un pequeño sesgo hacia usar source más tardío dentro de lo factible,
        # porque suele reducir inventario sin aumentar setups.
        source_bias = 0.01 * (t - s)

        return new_setup_penalty + consolidation + inventory + source_bias


def build_component(problem, consolidation_weight: float = 1.0, inventory_weight: float = 1.0, new_setup_weight: float = 1.0):
    return SetupConsolidationBias(
        problem,
        consolidation_weight=consolidation_weight,
        inventory_weight=inventory_weight,
        new_setup_weight=new_setup_weight,
    )
