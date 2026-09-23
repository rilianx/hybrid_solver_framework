from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "batch_covering_merge",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "merge_window": {"type": "int", "range": [1, 8]},
        "inventory_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class Constructor:
    """Constructor simple: crea setups en bloques de demanda y garantiza cobertura prefix por ítem."""

    def __init__(self, merge_window: int = 2, inventory_bias: float = 0.4):
        self.merge_window = merge_window
        self.inventory_bias = inventory_bias

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        for i in range(n_items):
            demand = inst.demand[i]
            if sum(demand) <= 1e-12:
                continue

            first = next((t for t in range(n_periods) if demand[t] > 1e-12), None)
            if first is not None:
                sol[i][first] = True

            # Construye bloques usando cobertura acumulada por tramo:
            # si la demanda acumulada del tramo supera la capacidad acumulada disponible
            # desde el último setup, se abre un nuevo setup en el período actual.
            last_setup = first
            if last_setup is not None:
                seg_demand = 0.0
                seg_cap = 0.0
                seg_setup_time = float(inst.setup_time[i])

                for t in range(first, n_periods):
                    seg_cap += float(inst.capacity[t])
                    if sol[i][t]:
                        # setup ya existente en el tramo
                        if t != first:
                            seg_setup_time += float(inst.setup_time[i])
                    dt = float(demand[t])
                    if dt > 1e-12:
                        seg_demand += dt

                    available = seg_cap - seg_setup_time
                    if seg_demand > available + 1e-12:
                        # hace falta un setup adicional en el período actual para repartir la producción
                        if not sol[i][t]:
                            sol[i][t] = True
                            seg_setup_time += float(inst.setup_time[i])
                            available = seg_cap - seg_setup_time
                        # reinicia el tramo desde este setup
                        last_setup = t
                        seg_demand = dt if dt > 1e-12 else 0.0
                        seg_cap = float(inst.capacity[t])
                        seg_setup_time = float(inst.setup_time[i])

        sol_tuple = tuple(tuple(row) for row in sol)

        # Reparación ligera: asegura que cada tramo de demanda sea cubierto por suficiente
        # capacidad acumulada entre setups, añadiendo setups elementales cuando haga falta.
        sol_tuple = self._repair(inst, sol_tuple, rng)

        return sol_tuple

    def _repair(self, inst: CLSPInstance, sol, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        solm = [list(row) for row in sol]

        for i in range(n_items):
            demand = inst.demand[i]
            if sum(demand) <= 1e-12:
                continue

            # Asegura al menos un setup en el primer período con demanda.
            if not any(solm[i]):
                first = next((t for t in range(n_periods) if demand[t] > 1e-12), None)
                if first is not None:
                    solm[i][first] = True

            setups = [t for t in range(n_periods) if solm[i][t]]
            if not setups:
                continue

            # Revisa cada segmento entre setups y añade un setup adicional si la demanda acumulada
            # supera la capacidad acumulada disponible en el segmento.
            augmented = True
            while augmented:
                augmented = False
                setups = [t for t in range(n_periods) if solm[i][t]]
                for idx, start in enumerate(setups):
                    end = setups[idx + 1] if idx + 1 < len(setups) else n_periods

                    seg_dem = 0.0
                    seg_cap = 0.0
                    seg_setup_time = 0.0

                    for t in range(start, end):
                        seg_cap += float(inst.capacity[t])
                        if solm[i][t]:
                            seg_setup_time += float(inst.setup_time[i])
                        dt = float(demand[t])
                        if dt > 1e-12:
                            seg_dem += dt

                        if seg_dem > seg_cap - seg_setup_time + 1e-12:
                            # abrir otro setup en el propio período t para repartir el tramo
                            if not solm[i][t]:
                                solm[i][t] = True
                                augmented = True
                                break
                    if augmented:
                        break

            # Evita dejar demanda estrictamente antes del primer setup.
            first_setup = next((t for t in range(n_periods) if solm[i][t]), None)
            if first_setup is not None:
                first_dem = next((t for t in range(n_periods) if demand[t] > 1e-12), None)
                if first_dem is not None and first_dem < first_setup:
                    solm[i][first_dem] = True

        return tuple(tuple(row) for row in solm)


def build_component(problem, merge_window: int = 2, inventory_bias: float = 0.4):
    return Constructor(merge_window=merge_window, inventory_bias=inventory_bias)
