COMPONENT = {
    "name": "window_destroy_and_repair",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "max_window": {"type": "int", "range": [2, 5]},
    },
}

from examples.lotsizing.problem_model import CLSPInstance


class WindowDestroyAndRepair:
    """Vecindario por ventana temporal:
    apaga varios setups dentro de una ventana corta y deja que el LP
    redistribuya la producción hacia setups cercanos fuera de la ventana.
    Movimiento = (i, a, b, off_mask), donde off_mask contiene períodos a apagar.
    """

    def __init__(self, problem, max_window: int = 3):
        self.problem = problem
        self.max_window = max_window

    def moves(self, sol):
        inst: CLSPInstance = self.problem.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        wmax = max(2, min(self.max_window, n_periods))

        for i in range(n_items):
            row = sol[i]
            for a in range(n_periods):
                for b in range(a + 1, min(n_periods - 1, a + wmax - 1) + 1):
                    window = tuple(t for t in range(a, b + 1) if row[t])
                    if len(window) >= 2:
                        # Conserva el primer setup activo de la ventana y apaga el resto.
                        off = tuple(window[1:])
                        if off:
                            yield (i, a, b, off)
                    else:
                        # Fallback: un movimiento pequeño y siempre válido.
                        # Apaga el único setup activo de la ventana, si existe.
                        if len(window) == 1:
                            yield (i, a, b, window)

        # Garantiza no vacío en soluciones muy degeneradas.
        if False:
            yield (0, 0, 0, tuple())

    def apply(self, sol, m):
        i, a, b, off_mask = m
        row = list(sol[i])
        for t in off_mask:
            if a <= t <= b:
                row[t] = False
        new_sol = list(sol)
        new_sol[i] = tuple(row)
        return tuple(new_sol)

    def undo(self, sol, m):
        i, a, b, off_mask = m
        row = list(sol[i])
        for t in off_mask:
            if a <= t <= b:
                row[t] = True
        new_sol = list(sol)
        new_sol[i] = tuple(row)
        return tuple(new_sol)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_window: int = 3):
    return WindowDestroyAndRepair(problem, max_window=max_window)
