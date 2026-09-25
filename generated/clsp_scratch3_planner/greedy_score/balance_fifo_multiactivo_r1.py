from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import math

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "balance_fifo_multiactivo",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "balance_weight": {"type": "float", "range": [0.0, 5.0]},
        "repeat_weight": {"type": "float", "range": [0.0, 5.0]},
        "setup_weight": {"type": "float", "range": [0.0, 3.0]},
        "lookback": {"type": "int", "range": [0, 10]},
    },
}


class BalanceFifoMultiactivo:
    """Greedy score para CLSP: favorece cubrir primero ítems más atrasados
    respecto a su demanda acumulada, y penaliza concentrar demasiadas acciones
    sobre el mismo ítem en un tramo temporal corto.

    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        balance_weight: float = 1.5,
        repeat_weight: float = 1.0,
        setup_weight: float = 0.5,
        lookback: int = 3,
    ):
        self.inst: CLSPInstance = problem.inst
        self.balance_weight = float(balance_weight)
        self.repeat_weight = float(repeat_weight)
        self.setup_weight = float(setup_weight)
        self.lookback = int(lookback)

        self._total_demand = tuple(sum(row) for row in self.inst.demand)
        self._grand_total = sum(self._total_demand)
        self._eps = 1e-9

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        i = action.item
        t = action.period
        s = action.source

        total_i = self._total_demand[i]
        pending_i = sum(partial.rem[i])
        served_i = total_i - pending_i

        # Urgencia relativa: cuánto le falta al ítem respecto a lo que ya acumula cubierto.
        # Si un ítem va más atrasado, su score baja.
        pending_ratio = pending_i / max(total_i, self._eps)
        served_ratio = served_i / max(total_i, self._eps)

        # Balance transversal: comparar el avance del ítem con el promedio global.
        pending_total = partial.pending_total()
        served_total = self._grand_total - pending_total
        global_ratio = served_total / max(self._grand_total, self._eps)

        # Queremos priorizar el que está más por detrás del promedio.
        lag = max(0.0, global_ratio - served_ratio)

        # Penalización por repetir el mismo ítem en un tramo corto temporal.
        # Cuenta setups recientes del mismo ítem alrededor de la fuente.
        repeat_count = 0
        if self.lookback > 0:
            lo = max(0, s - self.lookback)
            hi = min(self.inst.n_periods - 1, s + self.lookback)
            for tt in range(lo, hi + 1):
                if partial.setup[i][tt]:
                    repeat_count += 1

        # Si la acción requiere encender un setup nuevo, penalizamos un poco más
        # para no sesgar demasiado la construcción hacia el mismo ítem.
        setup_penalty = 1.0 if action.new_setup else 0.0

        # Preferimos acciones que cubren más cantidad de un ítem atrasado.
        qty_term = 1.0 / max(action.qty, self._eps)

        # No usar coste local: el criterio es balanceado y FIFO.
        score = (
            -self.balance_weight * (pending_ratio + lag)
            + self.repeat_weight * repeat_count
            + self.setup_weight * setup_penalty
            + 0.05 * qty_term
        )

        # Ligera preferencia FIFO por demandas más antiguas dentro del ítem.
        # Para un mismo ítem, cubrir periodos más tempranos es mejor.
        fifo_term = 0.01 * t

        # Penaliza en menor medida producir muy atrás si la fuente es muy temprana,
        # para evitar concentrar demasiadas acciones en el mismo tramo inicial.
        source_term = 0.005 * s

        return float(score + fifo_term + source_term)


def build_component(
    problem,
    balance_weight: float = 1.5,
    repeat_weight: float = 1.0,
    setup_weight: float = 0.5,
    lookback: int = 3,
):
    return BalanceFifoMultiactivo(
        problem,
        balance_weight=balance_weight,
        repeat_weight=repeat_weight,
        setup_weight=setup_weight,
        lookback=lookback,
    )
