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
    """Constructor por ventanas: detecta picos de demanda por ítem y coloca setups en torno a esos picos para cubrir bloques contiguos."""

    def __init__(self, window_size: int = 3, peak_threshold: float = 0.6):
        self.window_size = window_size
        self.peak_threshold = peak_threshold

    @staticmethod
    def _empty_solution(n_items: int, n_periods: int):
        return tuple(tuple(False for _ in range(n_periods)) for _ in range(n_items))

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        demand = inst.demand
        sol = [list(row) for row in self._empty_solution(n_items, n_periods)]

        for i in range(n_items):
            row = list(demand[i])
            total = sum(row)
            if total <= 0:
                continue

            # localizar picos locales/absolutos
            peak = max(range(n_periods), key=lambda t: row[t])
            peak_value = row[peak]

            # Si no hay estructura clara, al menos arrancar donde haya demanda.
            if peak_value <= 0:
                first = next((t for t in range(n_periods) if row[t] > 0), None)
                if first is not None:
                    sol[i][first] = True
                continue

            # Ventanas alrededor del pico: setup en periodos que concentran una fracción relevante de la demanda.
            target = self.peak_threshold * total
            acc = 0.0
            chosen = set()

            # Expandir desde el pico hacia ambos lados, priorizando demanda alta.
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

            # Garantía mínima: si hay demanda y no se eligió nada, usar el primer período con demanda.
            if not chosen:
                chosen.add(next(t for t in range(n_periods) if row[t] > 0))

            for t in chosen:
                sol[i][t] = True

        return tuple(tuple(row) for row in sol)


def build_component(problem, window_size: int = 3, peak_threshold: float = 0.6):
    return DemandPeakWindowInitializer(window_size=window_size, peak_threshold=peak_threshold)
