from random import Random

COMPONENT = {
    "name": "demand_peak_window_initializer",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "window_size": {"type": "int", "range": [1, 10]},
        "peak_threshold": {"type": "float", "range": [0.0, 1.0]},
    },
}


class DemandPeakWindowInitializer:
    """Constructor por ventanas: detecta picos de demanda por ítem y coloca setups en torno a esos picos para cubrir bloques contiguos.

    Versión corregida: garantiza que todo ítem con demanda positiva en t=0 tenga setup en t=0,
    y que cada ítem se abra, como mínimo, en su primer período con demanda positiva.
    """

    def __init__(self, window_size: int = 3, peak_threshold: float = 0.6):
        self.window_size = window_size
        self.peak_threshold = peak_threshold

    @staticmethod
    def _empty_solution(n_items: int, n_periods: int):
        return tuple(tuple(False for _ in range(n_periods)) for _ in range(n_items))

    @staticmethod
    def _first_positive_period(row):
        for t, val in enumerate(row):
            if val > 0:
                return t
        return None

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        demand = inst.demand
        sol = [list(row) for row in self._empty_solution(n_items, n_periods)]

        # Paso 1: setups obligatorios en el primer período con demanda positiva.
        # Esto corrige el caso crítico de t=0: toda demanda en t=0 debe estar cubierta por un setup en t=0.
        first_pos = []
        for i in range(n_items):
            fp = self._first_positive_period(demand[i])
            first_pos.append(fp)
            if fp is not None:
                sol[i][fp] = True

        # Paso 2: heurística de picos/ventanas para añadir algunos setups extra,
        # pero sin eliminar los obligatorios. Esto intenta mejorar la cobertura de lotes
        # con demanda dispersa, manteniendo la idea original.
        for i in range(n_items):
            row = list(demand[i])
            total = sum(row)
            if total <= 0:
                continue

            peak = max(range(n_periods), key=lambda t: row[t])
            peak_value = row[peak]
            if peak_value <= 0:
                continue

            target = self.peak_threshold * total
            acc = 0.0
            chosen = set()

            order = [peak]
            for step in range(1, self.window_size + 1):
                if peak - step >= 0:
                    order.append(peak - step)
                if peak + step < n_periods:
                    order.append(peak + step)

            order.sort(key=lambda t: (-row[t], abs(t - peak), t))
            for t in order:
                if row[t] <= 0:
                    continue
                chosen.add(t)
                acc += row[t]
                if acc >= target:
                    break

            # Nunca quitar el setup obligatorio del primer período con demanda.
            fp = first_pos[i]
            if fp is not None:
                chosen.add(fp)

            for t in chosen:
                sol[i][t] = True

        return tuple(tuple(row) for row in sol)


def build_component(problem, window_size: int = 3, peak_threshold: float = 0.6):
    return DemandPeakWindowInitializer(window_size=window_size, peak_threshold=peak_threshold)
