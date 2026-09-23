from random import Random
from typing import List

COMPONENT = {
    "name": "item_block_compaction_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 8.0]},
        "block_span": {"type": "int", "range": [1, 5]},
    },
}


class ItemBlockCompactionPerturbation:
    """Kicks by compacting or spreading the setups of one item over a short window."""

    def __init__(self, problem, block_span: int = 3):
        self.problem = problem
        self.inst = problem.inst
        self.block_span = max(1, int(block_span))

    def _set(self, sol, i: int, t: int, value: bool):
        rows = [list(row) for row in sol]
        rows[i][t] = value
        return tuple(tuple(row) for row in rows)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        k = max(1, int(round(strength)))

        # Pick an item with at least one setup if possible.
        items = list(range(n_items))
        rng.shuffle(items)
        chosen_i = None
        for i in items:
            if any(sol[i][t] for t in range(n_periods)):
                chosen_i = i
                break
        if chosen_i is None:
            chosen_i = rng.randrange(n_items)

        periods = [t for t in range(n_periods) if sol[chosen_i][t]]
        if not periods:
            t0 = rng.randrange(n_periods)
            return self._set(sol, chosen_i, t0, True)

        anchor = rng.choice(periods)
        start = max(0, anchor - rng.randrange(self.block_span))
        end = min(n_periods - 1, start + self.block_span - 1)

        new_sol = sol
        # Compact: keep only one setup in a local block and spread others outside it.
        block = list(range(start, end + 1))
        rng.shuffle(block)

        # First, ensure at least one bit changes inside the block.
        target_t = block[0]
        new_sol = self._set(new_sol, chosen_i, target_t, not new_sol[chosen_i][target_t])

        # Then perform a few additional changes guided by strength.
        for _ in range(k - 1):
            if rng.random() < 0.5 and len(periods) > 1:
                t = rng.choice(periods)
                u_choices = [u for u in range(n_periods) if u != t]
                u = rng.choice(u_choices)
                # Move a setup of the chosen item
                cand = self._set(new_sol, chosen_i, t, False)
                cand = self._set(cand, chosen_i, u, True)
                if cand != sol:
                    new_sol = cand
                    continue
            # Otherwise flip a nearby bit for a different item.
            j = rng.randrange(n_items)
            t = rng.choice(block) if block else rng.randrange(n_periods)
            cand = self._set(new_sol, j, t, not new_sol[j][t])
            if cand != sol:
                new_sol = cand

        if new_sol == sol:
            for i in range(n_items):
                for t in range(n_periods):
                    cand = self._set(sol, i, t, not sol[i][t])
                    if cand != sol:
                        return cand
        return new_sol


def build_component(problem, **params):
    block_span = params.get("block_span", 3)
    return ItemBlockCompactionPerturbation(problem, block_span=block_span)
