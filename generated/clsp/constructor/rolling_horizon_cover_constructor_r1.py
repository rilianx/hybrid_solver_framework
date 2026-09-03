from __future__ import annotations

from random import Random
from typing import List

COMPONENT = {
    "name": "rolling_horizon_cover_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class RollingHorizonCoverConstructor:
    """Construcción por ventana: cubre la demanda de cada ítem en bloques consecutivos hacia atrás, con setups compactados."""

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        y = [[False for _ in range(n_periods)] for _ in range(n_items)]
        remaining = [float(c) for c in inst.capacity]

        # Ventanas de cobertura de longitud variable: ítems con mayor setup_cost se compactan antes.
        items = list(range(n_items))
        items.sort(key=lambda i: (inst.setup_cost[i], sum(inst.demand[i]), -inst.holding_cost[i]), reverse=True)

        for i in items:
            total = sum(inst.demand[i])
            if total <= 1e-12:
                continue

            # Elegimos algunos períodos "ancla" con sesgo hacia demanda positiva y capacidad más holgada.
            anchors = list(range(n_periods))
            anchors.sort(key=lambda t: (inst.demand[i][t] > 0, remaining[t], -t), reverse=True)

            covered = 0.0
            selected = []
            for t in anchors:
                if covered >= total - 1e-12:
                    break
                # Intentamos abrir setup en t si cabe al menos una fracción razonable de la demanda remanente.
                if remaining[t] < float(inst.setup_time[i]) + 1e-12:
                    continue
                potential = remaining[t] - float(inst.setup_time[i])
                if potential <= 1e-12:
                    continue
                selected.append(t)
                y[i][t] = True
                remaining[t] -= float(inst.setup_time[i])
                take = min(potential, total - covered)
                remaining[t] -= take
                covered += take

            # Si aún falta cubrir demanda, usamos el mejor período disponible aunque sea menos elegante.
            if covered < total - 1e-12:
                for t in range(n_periods):
                    if covered >= total - 1e-12:
                        break
                    setup = float(inst.setup_time[i]) if not y[i][t] else 0.0
                    if remaining[t] < setup + 1e-12:
                        continue
                    if not y[i][t]:
                        y[i][t] = True
                        remaining[t] -= setup
                    take = min(remaining[t], total - covered)
                    if take > 1e-12:
                        remaining[t] -= take
                        covered += take

        return tuple(tuple(row) for row in y)


def build_component(problem, **params):
    return RollingHorizonCoverConstructor()
