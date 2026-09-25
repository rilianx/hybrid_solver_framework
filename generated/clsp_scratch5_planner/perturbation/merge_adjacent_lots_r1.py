from __future__ import annotations

from random import Random
from typing import Sequence

COMPONENT = {
    "name": "merge_adjacent_lots",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 5.0]},
    },
}


class MergeAdjacentLotsPerturbation:
    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def _copy_solution(self, sol):
        return tuple(tuple(row) for row in sol)

    def _period_load(self, sol, t: int) -> float:
        inst = self.inst
        return sum((inst.setup_time[i] if sol[i][t] else 0.0) + (inst.demand[i][t] if sol[i][t] else 0.0)
                   for i in range(inst.n_items))

    def _period_setup_time(self, sol, t: int) -> float:
        inst = self.inst
        return sum(inst.setup_time[i] for i in range(inst.n_items) if sol[i][t])

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return self._copy_solution(sol)

        k = max(1, int(round(strength)))
        k = min(k, n_periods)

        loads = [self._period_load(sol, t) for t in range(n_periods)]
        capacities = list(inst.capacity)
        slack = [capacities[t] - loads[t] for t in range(n_periods)]

        congested = sorted(range(n_periods), key=lambda t: (slack[t], -loads[t]))
        chosen_t = None
        for t in congested[: max(1, k)]:
            if any(sol[i][t] for i in range(n_items)):
                chosen_t = t
                break
        if chosen_t is None:
            chosen_t = rng.randrange(n_periods)

        # Cerca un período cercano con holgura.
        candidates = []
        for dt in range(1, n_periods):
            for sign in (-1, 1):
                tt = chosen_t + sign * dt
                if 0 <= tt < n_periods:
                    candidates.append(tt)
            if len(candidates) >= 4:
                break
        rng.shuffle(candidates)
        target_t = None
        for tt in candidates:
            if slack[tt] > 0 or tt != chosen_t:
                target_t = tt
                break
        if target_t is None:
            target_t = (chosen_t + 1) % n_periods

        # Selecciona un ítem con setup en el período congestionado y otro ítem para intercambiar.
        items_in_t = [i for i in range(n_items) if sol[i][chosen_t]]
        if not items_in_t:
            items_in_t = list(range(n_items))
        a = rng.choice(items_in_t)

        # Preferimos un ítem que tenga setup en target_t para realizar intercambio cruzado.
        items_in_target = [i for i in range(n_items) if sol[i][target_t] and i != a]
        if not items_in_target:
            # si no hay ítem en target, buscamos uno sin setup en t pero con setup en target o cualquier otro.
            items_in_target = [i for i in range(n_items) if i != a]
        b = rng.choice(items_in_target) if items_in_target else a

        new_sol = [list(row) for row in sol]

        # Movimiento base: intercambio cruzado de setups entre períodos cercanos.
        changed = False
        if chosen_t != target_t and sol[a][chosen_t]:
            new_sol[a][chosen_t] = False
            new_sol[a][target_t] = True
            changed = True

        if b != a and chosen_t != target_t:
            # Si el otro ítem tiene setup en target, lo movemos a chosen_t;
            # si no, lo activamos en chosen_t para forzar acoplamiento entre ítems.
            if sol[b][target_t]:
                new_sol[b][target_t] = False
                new_sol[b][chosen_t] = True
                changed = True
            else:
                if not new_sol[b][chosen_t]:
                    new_sol[b][chosen_t] = True
                    changed = True

        # Si el intercambio no produjo cambio, forzamos una reasignación mínima.
        if not changed:
            i = a
            t_from = chosen_t
            t_to = target_t if target_t != chosen_t else (chosen_t + 1) % n_periods
            new_sol[i][t_from] = not new_sol[i][t_from]
            new_sol[i][t_to] = not new_sol[i][t_to]

        # Pequeña intensificación: repetir en más períodos según strength.
        extra_moves = max(0, k - 1)
        for _ in range(extra_moves):
            t1 = rng.randrange(n_periods)
            t2 = (t1 + rng.choice([-1, 1])) % n_periods
            cand = [i for i in range(n_items) if new_sol[i][t1]]
            if not cand:
                continue
            i = rng.choice(cand)
            if t1 != t2:
                new_sol[i][t1] = False
                new_sol[i][t2] = True

        return tuple(tuple(row) for row in new_sol)


def build_component(problem, **params):
    strength = params.get("strength", 2.0)
    return MergeAdjacentLotsPerturbation(problem)
