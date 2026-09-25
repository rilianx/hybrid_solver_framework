from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "capacity_saturation_seed_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class CapacitySaturationSeedConstructor:
    """Constructor basado en saturación de capacidad: elige períodos "ancla" con más holgura y activa ahí los setups."""

    def __init__(self):
        pass

    @staticmethod
    def _all_true(inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _period_scores(self, inst: CLSPInstance) -> List[Tuple[float, int]]:
        # Score alto = mejor ancla: mucha capacidad, poca demanda agregada, y setups baratos.
        demand_by_t = [sum(inst.demand[i][t] for i in range(inst.n_items)) for t in range(inst.n_periods)]
        setup_time_total = sum(inst.setup_time)
        scores = []
        for t in range(inst.n_periods):
            slack_proxy = inst.capacity[t] - demand_by_t[t] - 0.5 * setup_time_total
            scores.append((slack_proxy, t))
        scores.sort(reverse=True)
        return scores

    def _seed_solution(self, inst: CLSPInstance, rng: Random) -> Tuple[Tuple[bool, ...], ...]:
        period_order = [t for _, t in self._period_scores(inst)]
        rows = [[False] * inst.n_periods for _ in range(inst.n_items)]

        # Ítems más "pesados" primero: mayor demanda total y mayor setup_time.
        item_order = list(range(inst.n_items))
        rng.shuffle(item_order)
        item_order.sort(
            key=lambda i: (
                -sum(inst.demand[i]),
                -inst.setup_time[i],
                inst.setup_cost[i],
            )
        )

        # Asignación de un ancla por ítem; si el ítem tiene demanda dispersa, pueden aparecer setups adicionales.
        for i in item_order:
            first_pos = next((t for t, d in enumerate(inst.demand[i]) if d > 0), 0)
            chosen = None
            for t in period_order:
                if t <= first_pos:
                    chosen = t
                    break
            if chosen is None:
                chosen = first_pos
            rows[i][chosen] = True

            # Complemento: si el horizonte es largo, añade un segundo setup a mitad de camino con baja probabilidad.
            if inst.n_periods >= 4:
                mid = max(chosen, min(inst.n_periods - 1, (chosen + inst.n_periods - 1) // 2))
                if mid != chosen and rng.random() < 0.4:
                    rows[i][mid] = True

        return tuple(tuple(r) for r in rows)

    def build(self, inst: CLSPInstance, rng: Random):
        model = LotSizingModel(inst)
        candidate = self._seed_solution(inst, rng)

        if model.is_feasible(candidate):
            return candidate

        # Fallback robusto: patrón denso completo.
        all_true = self._all_true(inst)
        if model.is_feasible(all_true):
            return all_true

        # Último intento: activar todos los setups de los ítems más críticos primero.
        current = candidate
        critical_items = sorted(range(inst.n_items), key=lambda i: (-sum(inst.demand[i]), -inst.setup_time[i]))
        for i in critical_items:
            trial = tuple(
                tuple((True if ii == i else current[ii][tt]) for tt in range(inst.n_periods))
                for ii in range(inst.n_items)
            )
            if model.is_feasible(trial):
                current = trial

        return current if model.is_feasible(current) else all_true


def build_component(problem, **params):
    return CapacitySaturationSeedConstructor()
