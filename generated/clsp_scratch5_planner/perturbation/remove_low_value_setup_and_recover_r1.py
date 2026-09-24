from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "remove_low_value_setup_and_recover",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 5.0]},
    },
}


class RemoveLowValueSetupAndRecover:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst = problem.inst

    def _setup_positions(self, sol):
        inst = self.inst
        return [
            [t for t in range(inst.n_periods) if sol[i][t]]
            for i in range(inst.n_items)
        ]

    def _candidate_score(self, i: int, t: int, sol) -> float:
        """
        Menor puntuación => setup menos valioso.
        Heurística local: preferimos apagar setups internos o aislados que
        cubren poca demanda incremental y que, si se eliminan, probablemente
        puedan ser absorbidos por el setup anterior con inventario.
        """
        inst = self.inst
        demands = inst.demand[i]
        s_cost = inst.setup_cost[i]
        h = inst.holding_cost[i]

        # No tocar el primer setup del ítem: suele ser estructural para arrancar.
        if not sol[i][t]:
            return float("inf")

        prev_on = None
        next_on = None
        for tt in range(t - 1, -1, -1):
            if sol[i][tt]:
                prev_on = tt
                break
        for tt in range(t + 1, inst.n_periods):
            if sol[i][tt]:
                next_on = tt
                break

        if prev_on is None:
            return float("inf")

        # Demanda que este setup "abastece" hasta el próximo setup (o fin).
        end = next_on if next_on is not None else inst.n_periods
        future_demand = sum(demands[tt] for tt in range(t, end))
        gap = (end - t)

        # Estimación grosera del coste de adelantar producción desde el setup anterior.
        # Si el bloque es corto y/o la demanda es pequeña, suele ser rentable eliminarlo.
        holding_penalty = h * future_demand * max(0, gap - 1) * 0.5

        # Penalizamos menos los setups muy cercanos al siguiente setup (más fáciles de absorber).
        neighborhood_bonus = 0.0
        if next_on is not None:
            neighborhood_bonus = 0.25 * h * sum(demands[t + 1:next_on])

        # Utilidad marginal aproximada: ahorro fijo - coste de inventario.
        return holding_penalty + neighborhood_bonus - s_cost

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods

        # Número de setups a eliminar: crece con strength pero acotado.
        raw_k = int(round(strength))
        k = max(1, min(raw_k, max(1, (n_items * n_periods) // 3)))

        # Construir lista de candidatos con puntuación.
        scored = []
        for i in range(n_items):
            for t in range(n_periods):
                if sol[i][t]:
                    score = self._candidate_score(i, t, sol)
                    if score != float("inf"):
                        scored.append((score, i, t))

        # Si no hay candidatos "buenos", caer a cualquier setup excepto el primero de cada ítem.
        if not scored:
            fallback = []
            for i in range(n_items):
                on = [t for t in range(n_periods) if sol[i][t]]
                for t in on[1:]:
                    fallback.append((0.0, i, t))
            scored = fallback

        if not scored:
            # Degenerado: cambiar un setup cualquiera para garantizar solución distinta.
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            new_sol = tuple(
                tuple((not sol[ii][tt]) if (ii == i and tt == t) else sol[ii][tt] for tt in range(n_periods))
                for ii in range(n_items)
            )
            return new_sol

        scored.sort(key=lambda x: x[0])

        # Selección sesgada: mejores candidatos, con algo de aleatoriedad.
        chosen = []
        used_items = set()
        pool = scored[: max(k * 4, 8)]

        while pool and len(chosen) < k:
            # Preferimos setups con menor utilidad marginal.
            weights = []
            for idx, (score, i, t) in enumerate(pool):
                if i in used_items:
                    weights.append(0.1)
                else:
                    weights.append(1.0 / (1.0 + max(0.0, score)))
            total = sum(weights)
            if total <= 0:
                break
            r = rng.random() * total
            acc = 0.0
            pick = 0
            for idx, w in enumerate(weights):
                acc += w
                if acc >= r:
                    pick = idx
                    break
            score, i, t = pool.pop(pick)
            if i in used_items:
                continue
            chosen.append((i, t))
            used_items.add(i)

        # Si aún faltan, completar con los mejores no usados.
        if len(chosen) < k:
            for _, i, t in scored:
                if i in used_items:
                    continue
                chosen.append((i, t))
                used_items.add(i)
                if len(chosen) >= k:
                    break

        # Aplicar destrucción: apagar setups seleccionados.
        new_sol = tuple(
            tuple(
                False if (i, t) in chosen else sol[i][t]
                for t in range(n_periods)
            )
            for i in range(n_items)
        )

        # Garantizar solución distinta para strength >= 1.
        if new_sol == sol:
            # Apagar un setup no inicial si existe; si no, cualquier setup.
            candidates = []
            for i in range(n_items):
                on = [t for t in range(n_periods) if sol[i][t]]
                for t in on[1:] if len(on) > 1 else on:
                    candidates.append((i, t))
            if candidates:
                i, t = candidates[rng.randrange(len(candidates))]
                new_sol = tuple(
                    tuple(False if (ii == i and tt == t) else sol[ii][tt] for tt in range(n_periods))
                    for ii in range(n_items)
                )
            else:
                i = rng.randrange(n_items)
                t = rng.randrange(n_periods)
                new_sol = tuple(
                    tuple((not sol[ii][tt]) if (ii == i and tt == t) else sol[ii][tt] for tt in range(n_periods))
                    for ii in range(n_items)
                )

        return new_sol


def build_component(problem, **params):
    strength = params.get("strength", 2.0)
    return RemoveLowValueSetupAndRecover(problem)
