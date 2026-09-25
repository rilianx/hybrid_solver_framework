from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "saturation_balancing_shift",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "window": {"type": "int", "range": [1, 12]},
        "shift_prob": {"type": "float", "range": [0.0, 1.0]},
        "prefer_early": {"type": "bool", "range": [0, 1]},
    },
}


class SaturationBalancingShift:
    """Constructor que reparte setups desde períodos saturados hacia períodos vecinos con holgura."""

    def __init__(self, window: int = 4, shift_prob: float = 0.7, prefer_early: bool = True):
        self.window = window
        self.shift_prob = shift_prob
        self.prefer_early = prefer_early

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # 1) Coloca un setup inicial para cada ítem con demanda en el período de mayor holgura local.
        for i in range(n_items):
            if sum(inst.demand[i]) <= 1e-12:
                continue
            best_t = 0
            best_score = None
            for t in range(n_periods):
                demand_ahead = sum(inst.demand[i][k] for k in range(t, min(n_periods, t + self.window)))
                slack = inst.capacity[t] - inst.setup_time[i]
                score = (slack - demand_ahead, -t if self.prefer_early else t)
                if best_score is None or score > best_score:
                    best_score = score
                    best_t = t
            sol[i][best_t] = True

        # 2) Añade setups extra donde la demanda acumulada futura supera la capacidad local.
        for i in range(n_items):
            cum = 0.0
            last = None
            for t in range(n_periods):
                cum += inst.demand[i][t]
                if sol[i][t]:
                    last = t
                if cum > 1e-12 and last is None and t > 0:
                    # Asegura cobertura del prefijo.
                    sol[i][t - 1] = True
                    last = t - 1

        # 3) Corrimiento: mueve setups desde períodos muy cargados a vecinos con más holgura.
        loads = [sum((inst.setup_time[i] if sol[i][t] else 0.0) + (inst.demand[i][t] if sol[i][t] else 0.0)
                     for i in range(n_items)) for t in range(n_periods)]

        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                if rng.random() > self.shift_prob:
                    continue

                candidates = []
                for dt in range(-self.window, self.window + 1):
                    if dt == 0:
                        continue
                    tt = t + dt
                    if tt < 0 or tt >= n_periods:
                        continue
                    if inst.capacity[tt] >= inst.setup_time[i] - 1e-12:
                        candidates.append(tt)

                # Mueve solo si mejora la "saturación" local.
                if not candidates:
                    continue
                candidates.sort(key=lambda tt: (loads[tt], tt if self.prefer_early else -tt))
                best_tt = candidates[0]
                if loads[best_tt] + 1e-9 < loads[t]:
                    sol[i][t] = False
                    sol[i][best_tt] = True
                    loads[best_tt] += inst.setup_time[i]
                    loads[t] -= inst.setup_time[i]

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

        # Reparación conservadora: garantiza al menos un setup por ítem con demanda, en un período factible.
        for i in range(n_items):
            if sum(inst.demand[i]) <= 1e-12:
                continue
            if not any(solm[i]):
                t = min(range(n_periods), key=lambda tt: (tt > 0, -inst.capacity[tt]))
                solm[i][t] = True

        return tuple(tuple(row) for row in solm)


def build_component(problem, window: int = 4, shift_prob: float = 0.7, prefer_early: bool = True):
    return SaturationBalancingShift(window=window, shift_prob=shift_prob, prefer_early=prefer_early)
