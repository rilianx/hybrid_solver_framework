from __future__ import annotations

from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "marginal_setup_savings",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "setup_weight": {"type": "float", "range": [0.0, 10.0]},
        "amortization_weight": {"type": "float", "range": [0.0, 10.0]},
        "holding_weight": {"type": "float", "range": [0.0, 5.0]},
        "consolidation_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class MarginalSetupSavings:
    """Puntúa acciones de cobertura privilegiando el ahorro marginal de setups.

    Idea:
    - Si la acción usa un setup ya activo, suele ser mejor: no paga costo fijo.
    - Si abre un setup nuevo, la acción es mejor cuanto más "amortiza" ese setup
      cubriendo más demanda pendiente del mismo ítem, especialmente si concentra
      producción futura en un mismo período.
    - Entre acciones similares, penaliza levemente adelantar producción mucho,
      porque introduce inventario extra.

    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem: Any,
        setup_weight: float = 1.0,
        amortization_weight: float = 1.0,
        holding_weight: float = 0.2,
        consolidation_weight: float = 0.5,
    ):
        self.inst: CLSPInstance = problem.inst
        self.setup_weight = setup_weight
        self.amortization_weight = amortization_weight
        self.holding_weight = holding_weight
        self.consolidation_weight = consolidation_weight

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i = action.item
        p = action.period
        s = action.source
        qty = action.qty

        setup_cost = inst.setup_cost[i]
        holding_cost = inst.holding_cost[i]

        # Demanda pendiente del mismo ítem desde el período cubierto en adelante.
        # Si es grande, el setup nuevo puede amortizarse mejor.
        rem_future = 0.0
        row = partial.rem[i]
        for t in range(p, inst.n_periods):
            rem_future += row[t]

        # Si el setup ya está activo en el source, priorizar fuertemente usarlo.
        if action.new_setup:
            setup_term = self.setup_weight * setup_cost
        else:
            setup_term = 0.0

        # Amortización del setup: cuanto más qty cubre respecto al costo fijo, mejor.
        amortization = setup_cost / max(qty, 1e-9)
        amort_term = self.amortization_weight * amortization

        # Penalización suave por adelantar producción e inventariar.
        lead = max(0, p - s)
        holding_term = self.holding_weight * holding_cost * qty * lead

        # Consolidación: si el ítem todavía tiene bastante demanda futura, abrir o usar
        # un setup en un período relativamente temprano puede consolidar más cobertura.
        # Queremos que más demanda futura reduzca el puntaje.
        consolidation_term = -self.consolidation_weight * (rem_future / max(setup_cost, 1.0))

        # Pequeño sesgo por preferir acciones que no abren setups nuevos si todo lo demás es similar.
        new_setup_term = self.setup_weight * (1.0 if action.new_setup else 0.0)

        # Prioridad principal: setups evitados / amortizados.
        return setup_term + amort_term + holding_term + consolidation_term + new_setup_term


def build_component(problem, setup_weight: float = 1.0, amortization_weight: float = 1.0, holding_weight: float = 0.2, consolidation_weight: float = 0.5):
    return MarginalSetupSavings(
        problem,
        setup_weight=setup_weight,
        amortization_weight=amortization_weight,
        holding_weight=holding_weight,
        consolidation_weight=consolidation_weight,
    )
