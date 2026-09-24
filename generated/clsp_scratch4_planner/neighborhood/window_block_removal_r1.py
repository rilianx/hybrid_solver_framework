COMPONENT = {
    "name": "window_block_removal",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "min_window": {"type": "int", "range": [2, 6]},
        "max_window": {"type": "int", "range": [2, 6]},
        "max_items": {"type": "int", "range": [1, 10]},
        "max_masks_per_window": {"type": "int", "range": [1, 32]},
    },
}


class WindowBlockRemoval:
    """Vecindario de destrucción local por ventana.

    Movimiento = (i, t0, length, mask), donde mask indica qué setups del ítem i
    dentro de la ventana [t0, t0+length-1] se apagan.
    """

    def __init__(self, problem, min_window=2, max_window=3, max_items=3, max_masks_per_window=8):
        self.problem = problem
        self.min_window = int(min_window)
        self.max_window = int(max_window)
        self.max_items = int(max_items)
        self.max_masks_per_window = int(max_masks_per_window)

    def _windows(self, n_periods):
        lo = max(1, min(self.min_window, self.max_window))
        hi = max(lo, min(self.max_window, n_periods))
        for length in range(lo, hi + 1):
            for t0 in range(0, n_periods - length + 1):
                yield t0, length

    def moves(self, sol):
        inst = self.problem.inst
        n_items, n_periods = inst.n_items, inst.n_periods

        items = []
        for i in range(n_items):
            count = sum(1 for t in range(n_periods) if sol[i][t])
            if count >= 2:
                items.append((count, i))
        items.sort()
        items = [i for _, i in items[: max(1, min(self.max_items, len(items)))]]

        yielded = 0
        for i in items:
            row = sol[i]
            for t0, length in self._windows(n_periods):
                positions = [p for p in range(length) if row[t0 + p]]
                if len(positions) < 1:
                    continue

                masks = []
                # Preferir máscaras contiguas o casi contiguas para "bloques"
                full_mask = (1 << length) - 1
                for mask in range(1, full_mask + 1):
                    if mask == full_mask:
                        continue
                    if mask.bit_count() == 0:
                        continue
                    # Solo apagar setups que existan en la ventana
                    if any(((mask >> p) & 1) and not row[t0 + p] for p in range(length)):
                        continue
                    # Evitar vecindad trivial de apagar un único setup aislado si hay bloque posible
                    if mask.bit_count() == 1 and len(positions) > 1:
                        continue
                    masks.append(mask)

                # Priorizar máscaras más "bloque"
                masks.sort(key=lambda m: (abs(m.bit_count() - max(2, len(positions) // 2)), -m.bit_count(), m))
                for mask in masks[: self.max_masks_per_window]:
                    yield (i, t0, length, mask)
                    yielded += 1
                    if yielded >= 10000:
                        return

    def apply(self, sol, m):
        i, t0, length, mask = m
        s = [list(row) for row in sol]
        for p in range(length):
            if (mask >> p) & 1:
                s[i][t0 + p] = False
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t0, length, mask = m
        s = [list(row) for row in sol]
        for p in range(length):
            if (mask >> p) & 1:
                s[i][t0 + p] = True
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    defaults = {
        "min_window": 2,
        "max_window": 3,
        "max_items": 3,
        "max_masks_per_window": 8,
    }
    cfg = {**defaults, **params}
    return WindowBlockRemoval(problem, **cfg)
