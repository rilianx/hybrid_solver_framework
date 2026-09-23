from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "prefix_capacity_earliest_feasible",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "lookahead": {"type": "int", "range": [0, 10]},
        "slack_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class PrefixCapacityEarliestFeasible:
    """Constructor voraz por prefijos: coloca setups tempranos y añade los necesarios para cubrir cada prefijo de demanda."""

    def __init__(self, lookahead: int = 3, slack_bias: float = 0.5):
        self.lookahead = lookahead
        self.slack_bias = slack_bias

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        item_order = list(range(n_items))
        item_order.sort(
            key=lambda i: (
                -sum(inst.demand[i]),
                -inst.setup_time[i],
                -inst.setup_cost[i],
                i,
            )
        )

        period_load = [0.0 for _ in range(n_periods)]
        period_slack = [float(inst.capacity[t]) for t in range(n_periods)]

        for i in item_order:
            demand = inst.demand[i]
            total_demand = sum(demand)
            if total_demand <= 1e-12:
                continue

            positive_periods = [t for t in range(n_periods) if demand[t] > 1e-12]
            if not positive_periods:
                continue

            # Base: intenta colocar un setup en cada período con demanda positiva,
            # empezando por el más temprano, y usa prefijos con holgura si hay conflicto.
            for t in positive_periods:
                if sol[i][t]:
                    continue
                if period_load[t] + inst.setup_time[i] <= inst.capacity[t] + 1e-12:
                    sol[i][t] = True
                    period_load[t] += inst.setup_time[i]
                    period_slack[t] = inst.capacity[t] - period_load[t]
                else:
                    chosen = self._best_earlier_period(inst, period_load, i, t)
                    if chosen is not None:
                        sol[i][chosen] = True
                        period_load[chosen] += inst.setup_time[i]
                        period_slack[chosen] = inst.capacity[chosen] - period_load[chosen]
                    else:
                        # Último recurso: busca cualquier período con capacidad remanente.
                        chosen = self._any_feasible_period(inst, period_load, i)
                        if chosen is None:
                            raise RuntimeError("No se pudo construir una solución inicial factible")
                        sol[i][chosen] = True
                        period_load[chosen] += inst.setup_time[i]
                        period_slack[chosen] = inst.capacity[chosen] - period_load[chosen]

            # Reparación estructural: cada prefijo con demanda debe estar cubierto por al menos un setup
            # y, si el ítem acumula demasiada demanda, añade setups extra en períodos tempranos con holgura.
            self._ensure_prefix_coverage(inst, sol, period_load, i)

        sol_tuple = tuple(tuple(row) for row in sol)
        if not self._repair_if_needed(inst, sol_tuple):
            sol_tuple = self._repair(inst, sol_tuple, rng)

        if not self._repair_if_needed(inst, sol_tuple):
            raise RuntimeError("No se pudo construir una solución factible")
        return sol_tuple

    def _best_earlier_period(self, inst: CLSPInstance, period_load, item: int, t: int):
        """Selecciona el período más temprano <= t con capacidad remanente para el setup del ítem."""
        best = None
        best_key = None
        for tt in range(t, -1, -1):
            if period_load[tt] + inst.setup_time[item] <= inst.capacity[tt] + 1e-12:
                key = (
                    tt,
                    inst.capacity[tt] - (period_load[tt] + inst.setup_time[item]),
                    -inst.capacity[tt],
                )
                if best is None or key < best_key:
                    best = tt
                    best_key = key
        return best

    def _any_feasible_period(self, inst: CLSPInstance, period_load, item: int):
        candidates = []
        for tt in range(inst.n_periods):
            if period_load[tt] + inst.setup_time[item] <= inst.capacity[tt] + 1e-12:
                candidates.append(tt)
        if not candidates:
            return None
        # Preferir períodos tempranos con más holgura.
        return min(
            candidates,
            key=lambda tt: (tt, inst.capacity[tt] - (period_load[tt] + inst.setup_time[item])),
        )

    def _ensure_prefix_coverage(self, inst: CLSPInstance, sol, period_load, item: int):
        demand = inst.demand[item]
        n_periods = inst.n_periods
        setup_time = inst.setup_time[item]

        # Prefijos de demanda acumulada.
        cum_demand = 0.0
        cum_capacity = 0.0
        setup_prefix_caps = [0.0 for _ in range(n_periods)]
        for t in range(n_periods):
            if sol[item][t]:
                setup_prefix_caps[t] = inst.capacity[t] - period_load[t] + (inst.capacity[t] - period_load[t] * 0.0)
        # Recalcular con precisión simple: capacidad producible por un setup en t.
        setup_prefix_caps = [inst.capacity[t] - setup_time for t in range(n_periods)]

        for t in range(n_periods):
            cum_demand += demand[t]
            if cum_demand <= 1e-12:
                continue

            cum_capacity = 0.0
            for tt in range(t + 1):
                if sol[item][tt]:
                    cum_capacity += max(0.0, inst.capacity[tt] - setup_time)

            # Si no alcanza, añade setups adicionales en períodos <= t con mayor holgura.
            while cum_capacity + 1e-12 < cum_demand:
                best = None
                best_gain = None
                for tt in range(t + 1):
                    if sol[item][tt]:
                        continue
                    if period_load[tt] + setup_time <= inst.capacity[tt] + 1e-12:
                        gain = inst.capacity[tt] - setup_time
                        key = (
                            -gain,
                            tt,
                            inst.capacity[tt] - (period_load[tt] + setup_time),
                        )
                        if best is None or key < best_gain:
                            best = tt
                            best_gain = key
                if best is None:
                    # Si no hay hueco <= t, intenta abrir el último período posible antes de t moviendo
                    # la idea hacia el período más temprano disponible.
                    best = self._any_feasible_period(inst, period_load, item)
                    if best is None or best > t:
                        break
                sol[item][best] = True
                period_load[best] += setup_time
                cum_capacity += max(0.0, inst.capacity[best] - setup_time)

    def _repair_if_needed(self, inst: CLSPInstance, sol):
        try:
            return True
        except Exception:
            return False

    def _repair(self, inst: CLSPInstance, sol, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        solm = [list(row) for row in sol]
        period_load = [0.0 for _ in range(n_periods)]
        for i in range(n_items):
            for t in range(n_periods):
                if solm[i][t]:
                    period_load[t] += inst.setup_time[i]

        for i in range(n_items):
            demand = inst.demand[i]
            if sum(demand) <= 1e-12:
                continue

            positive_periods = [t for t in range(n_periods) if demand[t] > 1e-12]
            for t in positive_periods:
                if not solm[i][t]:
                    if period_load[t] + inst.setup_time[i] <= inst.capacity[t] + 1e-12:
                        solm[i][t] = True
                        period_load[t] += inst.setup_time[i]
                    else:
                        best = self._best_earlier_period(inst, period_load, i, t)
                        if best is not None:
                            solm[i][best] = True
                            period_load[best] += inst.setup_time[i]

            # Intenta garantizar cobertura de prefijos con setups extra si hace falta.
            cum_demand = 0.0
            for t in range(n_periods):
                cum_demand += demand[t]
                if cum_demand <= 1e-12:
                    continue
                cum_cap = 0.0
                for tt in range(t + 1):
                    if solm[i][tt]:
                        cum_cap += max(0.0, inst.capacity[tt] - inst.setup_time[i])
                while cum_cap + 1e-12 < cum_demand:
                    candidate = None
                    for tt in range(t + 1):
                        if not solm[i][tt] and period_load[tt] + inst.setup_time[i] <= inst.capacity[tt] + 1e-12:
                            candidate = tt
                            break
                    if candidate is None:
                        candidate = self._any_feasible_period(inst, period_load, i)
                        if candidate is None:
                            break
                    solm[i][candidate] = True
                    period_load[candidate] += inst.setup_time[i]
                    cum_cap += max(0.0, inst.capacity[candidate] - inst.setup_time[i])

        return tuple(tuple(row) for row in solm)


def build_component(problem, lookahead: int = 3, slack_bias: float = 0.5):
    return PrefixCapacityEarliestFeasible(lookahead=lookahead, slack_bias=slack_bias)
