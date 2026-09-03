from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "randomized_window_rcl_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {"alpha": {"type": "float", "range": [0.1, 1.0]}},
}


class RandomizedWindowRCLConstructor:
    """GRASP temporal: elige ventanas de producción y resuelve por una lista restringida aleatoria."""

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha

    def _candidate_score(self, inst: CLSPInstance, i: int, a: int, b: int) -> float:
        demand = sum(inst.demand[i][t] for t in range(a, b + 1))
        # Menor score = mejor: privilegia lots grandes con setups caros y holding bajo.
        return (inst.setup_cost[i] + inst.setup_time[i]) / max(1e-9, demand) + 0.1 * inst.holding_cost[i] * (b - a)

    def _construct(self, inst: CLSPInstance, rng: Random):
        n, T = inst.n_items, inst.n_periods
        sol = [[False] * T for _ in range(n)]
        residual = [float(c) for c in inst.capacity]

        # Ventanas aleatorias de longitud variable.
        windows = []
        t = 0
        while t < T:
            w = 1 + int(rng.random() * max(1, T // 3))
            windows.append((t, min(T - 1, t + w - 1)))
            t += w

        for a, b in windows:
            items = list(range(n))
            items.sort(key=lambda i: self._candidate_score(inst, i, a, b))
            rcl_size = max(1, int(len(items) * self.alpha))
            chosen = items[:rcl_size]
            rng.shuffle(chosen)

            for i in chosen:
                demand = sum(inst.demand[i][t] for t in range(a, b + 1))
                need = inst.setup_time[i] + demand
                if need <= residual[a] + 1e-9:
                    sol[i][a] = True
                    residual[a] -= need

            # Completa con ítems forzados si queda demanda futura sin ningún setup.
            for i in range(n):
                if any(sol[i][t] for t in range(a, b + 1)):
                    continue
                future = sum(inst.demand[i][t] for t in range(a, b + 1))
                if future > 1e-9 and inst.setup_time[i] + future <= residual[a] + 1e-9:
                    sol[i][a] = True
                    residual[a] -= inst.setup_time[i] + future

        return tuple(tuple(r) for r in sol)

    def _repair(self, problem, inst: CLSPInstance, sol):
        if problem.is_feasible(sol):
            return sol

        n, T = inst.n_items, inst.n_periods
        current = [list(r) for r in sol]

        # Reparación diversa: intenta abrir setups en la primera mitad de los períodos
        # para dar margen de inventario.
        for _ in range(n * T * 4):
            trial = tuple(tuple(r) for r in current)
            if problem.is_feasible(trial):
                return trial

            best = None
            best_obj = None
            for i in range(n):
                for t in range(T):
                    if current[i][t]:
                        continue
                    cand = [row[:] for row in current]
                    cand[i][t] = True
                    cand_sol = tuple(tuple(r) for r in cand)
                    obj = problem.objective(cand_sol)
                    if best_obj is None or obj < best_obj:
                        best_obj = obj
                        best = cand
            if best is None:
                break
            current = best

        return tuple(tuple(r) for r in current)

    def build(self, inst: CLSPInstance, rng: Random):
        raise RuntimeError("use build_component")


def build_component(problem, alpha: float = 0.3):
    class _B(RandomizedWindowRCLConstructor):
        def build(self, inst: CLSPInstance, rng: Random):
            sol = self._construct(inst, rng)
            return self._repair(problem, inst, sol)

    return _B(alpha=alpha)
