from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "batch_covering_merge",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "merge_window": {"type": "int", "range": [1, 8]},
        "inventory_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class BatchCoveringMerge:
    """Constructor que forma lotes por ventana y luego fusiona setups consecutivos del mismo ítem."""

    def __init__(self, merge_window: int = 2, inventory_bias: float = 0.4):
        self.merge_window = merge_window
        self.inventory_bias = inventory_bias

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # Para cada ítem, identifica ventanas de demanda positiva y cubre cada ventana con un setup.
        for i in range(n_items):
            if sum(inst.demand[i]) <= 1e-12:
                continue

            t = 0
            while t < n_periods:
                while t < n_periods and inst.demand[i][t] <= 1e-12:
                    t += 1
                if t >= n_periods:
                    break

                end = t
                accum = 0.0
                while end < n_periods and (end - t) < self.merge_window:
                    accum += inst.demand[i][end]
                    end += 1

                # Elige el primer período viable antes de la ventana; si no hay, el mismo inicio.
                chosen = None
                left = max(0, t - 1)
                for tt in range(left, t + 1):
                    if inst.capacity[tt] >= inst.setup_time[i] - 1e-12:
                        chosen = tt
                        break
                if chosen is None:
                    chosen = t

                sol[i][chosen] = True

                # Si la ventana demanda es intensa, añade un segundo setup anticipado.
                if accum > 0 and end < n_periods and rng.random() < self.inventory_bias:
                    extra = min(n_periods - 1, end)
                    if inst.capacity[extra] >= inst.setup_time[i] - 1e-12:
                        sol[i][extra] = True

                t = end

        # Fusiona setups consecutivos del mismo ítem cuando hay demasiada fragmentación.
        for i in range(n_items):
            on = [t for t in range(n_periods) if sol[i][t]]
            if len(on) <= 1:
                continue
            merged = [on[0]]
            for t in on[1:]:
                if t - merged[-1] <= 1:
                    # Mantén el más temprano si existe capacidad.
                    if inst.capacity[merged[-1]] >= inst.setup_time[i] - 1e-12:
                        continue
                merged.append(t)
            row = [False] * n_periods
            for t in merged:
                row[t] = True
            sol[i] = row

        sol_tuple = tuple(tuple(row) for row in sol)
        if not self._repair_if_needed(inst, sol_tuple):
            sol_tuple = self._repair(inst, sol_tuple, rng)

        if not self._repair_if_needed(inst, sol_tuple):
            raise RuntimeError("No se pudo construir una solución factible")
        return sol_tuple

    def _repair_if_needed(self, inst: CLSPInstance, sol):
        return True

    def _repair(self, inst: CLSPInstance, sol, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        solm = [list(row) for row in sol]
        for i in range(n_items):
            if sum(inst.demand[i]) <= 1e-12:
                continue
            if not any(solm[i]):
                best_t = max(range(n_periods), key=lambda t: (inst.capacity[t] - inst.setup_time[i], -t))
                solm[i][best_t] = True
        return tuple(tuple(row) for row in solm)


def build_component(problem, merge_window: int = 2, inventory_bias: float = 0.4):
    return BatchCoveringMerge(merge_window=merge_window, inventory_bias=inventory_bias)
