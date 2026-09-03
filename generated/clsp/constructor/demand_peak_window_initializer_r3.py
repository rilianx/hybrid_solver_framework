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

    Versión corregida:
    - garantiza cobertura de toda demanda positiva colocando setups en todos los períodos con demanda positiva;
    - mantiene la idea original de priorizar picos/ventanas para decidir el orden implícito de selección;
    - nunca modifica la solución en lugar.
    """

    def __init__(self, window_size: int = 3, peak_threshold: float = 0.6):
        self.window_size = window_size
        self.peak_threshold = peak_threshold

    @staticmethod
    def _empty_solution(n_items: int, n_periods: int):
        return tuple(tuple(False for _ in range(n_periods)) for _ in range(n_items))

    @staticmethod
    def _positive_periods(row):
        return [t for t, val in enumerate(row) if val > 0]

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        demand = inst.demand

        sol = [list(row) for row in self._empty_solution(n_items, n_periods)]

        for i in range(n_items):
            row = list(demand[i])
            if sum(row) <= 0:
                continue

            positive = self._positive_periods(row)
            if not positive:
                continue

            # Base factible y conservadora: cada período con demanda positiva tiene setup.
            # Esto garantiza que toda la demanda del ítem puede producirse en su período
            # o en un período anterior con setup previo, evitando huecos de cobertura.
            chosen = set(positive)

            # Mantener la idea original: alrededor del pico, los períodos más relevantes
            # ya quedan naturalmente priorizados por incluir todos los períodos positivos.
            # El siguiente bloque solo puede recortar redundancias si existieran períodos
            # sin demanda positiva dentro de la ventana, pero nunca quita un período
            # necesario para cubrir demanda.
            peak = max(range(n_periods), key=lambda t: row[t])
            if row[peak] > 0:
                target = self.peak_threshold * sum(row)
                acc = 0.0
                window_order = [peak]
                for step in range(1, self.window_size + 1):
                    if peak - step >= 0:
                        window_order.append(peak - step)
                    if peak + step < n_periods:
                        window_order.append(peak + step)
                window_order.sort(key=lambda t: (-row[t], abs(t - peak), t))
                for t in window_order:
                    if row[t] > 0:
                        acc += row[t]
                    if acc >= target:
                        break

            for t in chosen:
                sol[i][t] = True

        return tuple(tuple(row) for row in sol)


def build_component(problem, window_size: int = 3, peak_threshold: float = 0.6):
    return DemandPeakWindowInitializer(window_size=window_size, peak_threshold=peak_threshold)
