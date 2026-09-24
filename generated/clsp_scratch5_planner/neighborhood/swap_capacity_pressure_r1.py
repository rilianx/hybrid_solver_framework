COMPONENT = {
    "name": "swap_capacity_pressure",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "window": {"type": "int", "range": [1, 2]},
        "max_moves": {"type": "int", "range": [1, 5000]},
    },
}


class SwapCapacityPressureNeighborhood:
    """Intercambio estructural de setups entre dos ítems y períodos cercanos.

    Movimiento:
      ("swap", i, j, t, tp)
    que intercambia la presencia de i y j entre los períodos t y tp:
      y[i,t], y[j,tp] se apagan
      y[i,tp], y[j,t] se encienden

    Si alguno de los cuatro cambios es redundante, sigue siendo un movimiento
    pequeño y perfectamente invertible.
    """

    def __init__(self, problem, window: int = 1, max_moves: int = 5000):
        self.problem = problem
        self.window = int(window)
        self.max_moves = int(max_moves)

    def _candidates(self, sol):
        inst = self.problem.inst
        n_items = inst.n_items
        n_periods = inst.n_periods

        # Periodos con presión de capacidad: priorizamos los más cargados.
        pressure = []
        for t in range(n_periods):
            used = sum(inst.setup_time[i] for i in range(n_items) if sol[i][t])
            pressure.append((used / max(inst.capacity[t], 1e-9), t))
        pressure.sort(reverse=True)
        periods = [t for _, t in pressure[: max(1, min(n_periods, 3 * self.window + 2))]]

        for t in periods:
            for dt in range(-self.window, self.window + 1):
                if dt == 0:
                    continue
                tp = t + dt
                if tp < 0 or tp >= n_periods:
                    continue
                for i in range(n_items):
                    for j in range(n_items):
                        if i == j:
                            continue
                        # swap between (i,t) and (j,tp)
                        if sol[i][t] != sol[j][tp]:
                            yield ("swap", i, j, t, tp)
                        else:
                            # Even if the pure swap is neutral, keeping it in the
                            # neighborhood preserves structure; the evaluator can
                            # still find improving variants on the instance.
                            yield ("swap", i, j, t, tp)

    def moves(self, sol):
        count = 0
        seen = set()
        for m in self._candidates(sol):
            if m in seen:
                continue
            seen.add(m)
            yield m
            count += 1
            if count >= self.max_moves:
                return

    def apply(self, sol, m):
        _, i, j, t, tp = m
        s = [list(row) for row in sol]
        s[i][t] = not s[i][t]
        s[j][tp] = not s[j][tp]
        s[i][tp] = not s[i][tp]
        s[j][t] = not s[j][t]
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        # Inverse of a symmetric swap is the same move.
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    window = params.get("window", 1)
    max_moves = params.get("max_moves", 5000)
    return SwapCapacityPressureNeighborhood(problem, window=window, max_moves=max_moves)
