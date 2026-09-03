COMPONENT = {
    "name": "run_compression",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "min_run": {"type": "int", "range": [2, 6]},
    },
}


class RunCompression:
    """Vecindario híbrido basado en compresión de rachas de setups.

    Movimiento principal: para una racha consecutiva de True en un ítem,
    apaga un sufijo de la racha.

    Para garantizar no vaciedad del vecindario en soluciones sin rachas
    de longitud suficiente, también se permiten movimientos elementales
    de activación/desactivación de un único setup.
    """

    def __init__(self, problem, min_run=2):
        self.problem = problem
        self.min_run = int(min_run)

    def moves(self, sol):
        inst = self.problem.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        L = max(2, self.min_run)

        found = False

        # Movimientos de compresión de rachas
        for i in range(n_items):
            t = 0
            while t < n_periods:
                if not sol[i][t]:
                    t += 1
                    continue
                a = t
                while t + 1 < n_periods and sol[i][t + 1]:
                    t += 1
                b = t
                run_len = b - a + 1
                if run_len >= L:
                    found = True
                    for cut in range(a + 1, b + 1):
                        yield ("compress", i, a, cut)
                t += 1

        # Si no hay compresiones posibles, asegurar no-vaciedad con
        # movimientos elementales de un solo setup.
        if not found:
            for i in range(n_items):
                for t in range(n_periods):
                    yield ("toggle", i, t)

    def apply(self, sol, m):
        kind = m[0]
        rows = [list(row) for row in sol]

        if kind == "compress":
            _, i, a, cut = m
            for t in range(cut, len(rows[i])):
                rows[i][t] = False
        elif kind == "toggle":
            _, i, t = m
            rows[i][t] = not rows[i][t]
        else:
            raise ValueError(f"Movimiento desconocido: {m!r}")

        return tuple(tuple(row) for row in rows)

    def undo(self, sol, m):
        # Los movimientos son involutivos: aplicar de nuevo revierte el cambio.
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    min_run = params.get("min_run", 2)
    return RunCompression(problem, min_run=min_run)
